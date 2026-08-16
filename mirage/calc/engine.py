from dataclasses import dataclass
import functools
from abc import ABC, abstractmethod
from typing import Iterator, Self
import logging
import logging.handlers
from multiprocessing import Process
import multiprocessing

from mirage.sim import Simulation, Experiment
from mirage.calc import Reducer
from mirage.util import (
  BidiStream,
  Stopwatch,
  VariantKey,
  bind_logging_to_queue,
  Dictify,
  ClusterProvider,
  LocalClusterProvider
)
from mirage.settings import load_settings

logger = logging.getLogger(__name__)

_STREAM_BUFFER_SZ = 4


@dataclass
class ResultKey:
  reducer_name: str
  simulation_key: VariantKey

  def __str__(self, *args, **kwargs) -> str:
    return f"ResultKey(reducer_name={self.reducer_name}, simulation_key={self.simulation_key})"

  def __repr__(self, *args, **kwargs) -> str:
    return str(self)


@dataclass
class ReducerResult:
  result_key: ResultKey
  reducer: Reducer
  cache_key: ResultKey | None = None


class ResultCalculator(ABC):
  @abstractmethod
  def initialize(self) -> None:
    """
    Function called once before running an experiment.

    This should raise an Exception if the ResultCalculator could not be
    initialized.
    """

  @abstractmethod
  def raytrace(self, simulation: Simulation) -> None:
    """
    Called when the Engine needs the ResultCalculator to trace rays. This
    method should have a side-effect of storing the resultant rays inside
    the instance state so that subsequent calls to apply_reducer() do not
    have to raytrace the Simulation again.


    This function may be called multiple times, in which case it is safe to
    discard internal state from prior calls.
    """

  @abstractmethod
  def apply_reducer(self, reducer: Reducer) -> Reducer:
    """
    Apply the specified reducer and return a reference to the hydrated
    version. This may or mahy not be the same instance as what was passed in.
    """

  def apply_all_reducers(self, reducers: Iterator[Reducer], callback: Callable[Reducer, None]) -> None:
    """
    Apply all reducers in a batch operation. Once applied, the callback
    function should be called with each computed reducer.

    Default implementation calls apply_reducer() on each reducer.
    """
    for reducer in reducers:
        callback(self.apply_reducer(reducer))


class _CachingCalculator:
  def __init__(self, result_calculator: ResultCalculator):
    self.result_calculator = result_calculator
    self.ray_traced_simulation = None
    self.simulation_cache_misses = -1
    self.reducer_dups = 0
    self.scheduled_reducers: list[ReducerResult] = []
    self.aliased_reducers: list[ReducerResult] = []

  def initialize(self) -> None:
    self.result_calculator.initialize()
    self.simulation_cache_misses = -1

  def deinit(self) -> None:
    self.result_calculator.deinit()

  def raytrace(self, simulation: Simulation) -> bool:
    if self.ray_traced_simulation is not None and self.ray_traced_simulation.is_similar(
      simulation
    ):
      return False
    self.ray_traced_simulation = simulation
    self.result_calculator.raytrace(simulation)
    self.scheduled_reducers = []
    self.aliased_reducers = []
    self.simulation_cache_misses += 1
    return True

  def schedule_reducer(self, reducer: Reducer, result_key: ResultKey) -> None:
    """
    Adds the reducer to the set of Reducers to be calculated.

    If the reducer equates to a reducer already scheduled it will NOT be recomputed,
    and will share the result of the existing reducer.
    """
    for reducer_result in self.scheduled_reducers:
        if Dictify.to_dict(reducer) == Dictify.to_dict(reducer_result.reducer):
            self.reducer_dups += 1
            self.aliased_reducers.append(ReducerResult(
              result_key, reducer_result.reducer, cache_key=reducer_result.result_key
            ))
            return
    self.scheduled_reducers.append(ReducerResult(result_key, reducer))

  def compute_reducers(self) -> Iterator[ReducerResult]:
      """
      Computes all scheduled reducers, and returns the results with aliased reducers
      as well.
      """
      consumed_aliases = set()
      reducers_arr = [r.reducer for r in self.scheduled_reducers]
      applied_reducers = self.result_calculator.apply_all_reducers(reducers_arr)
      for reducer, reducer_result in zip(applied_reducers, self.scheduled_reducers):
          reducer_result.reducer = reducer
          yield reducer_result
          for i, alias in enumerate(self.aliased_reducers):
              if i in consumed_aliases:
                  continue
              if Dictify.to_dict(alias.reducer) == Dictify.to_dict(reducer):
                  alias.reducer = reducer
                  consumed_aliases.add(i)
                  yield alias


class Engine:
  """
  Asynchronous engine for computing Gravitational lensing results.

  The engine is started in a separate thread, and then requests for calculations
  are done by writing and reading from its BidiStream.

  Calculations are done in a FIFO order, and only one calculation may be
  done at a time.



  Use-cases:

  1. Batch-instruction.
    a. Input is an Experiment or Simulation object
    b. Output is a zipfile written to-disk.
    c. Blocking is fine / preferred.
  2. Interractive (ipython) oneshot simulations.
    a. Input is an Experiment or Simulation object.
    b. Output is returned in-memory and / or written to-disk
    c. Blocking is fine / preferred, but may need a non-blocking api.
  3. GUI real-time visualizations.
    a. Input is a Simulation object.
    b. Output is in-memory only.
    c. Blocking is NOT ok.

  So we can do two APIs:

  ## Asynchronous API:

  run_experiment() or run_simulation() that returns the number of expected
  results, then the client has to sit and wait in a loop for when all the results
  are done.

  Example:

  ```
  for _ in range(engine.run_simulation(simulation)):
    result = engine.get_result()
  ```

  """

  def __init__(self, stream: BidiStream, engine_process: Process) -> None:
    self._stream = stream
    self._engine_process = engine_process

  @classmethod
  @functools.cache
  def create_default(cls) -> Self:
    from mirage.calc.dask_result_calculator import DaskResultCalculator
    cluster_provider = None
    try:
      cluster_provider = load_settings(ClusterProvider)
    except (EnvironmentError, ValueError):
      cluster_provider = LocalClusterProvider()
    dask_result_calculator = DaskResultCalculator(cluster_provider)
    return cls.create_and_start(dask_result_calculator)


  @classmethod
  def create_and_start(cls, calculator: ResultCalculator) -> Self:
    send, recv = BidiStream.create(_STREAM_BUFFER_SZ)
    queue_logger = logging.getHandlerByName("queue_handler")
    caching_calculator = _CachingCalculator(calculator)
    engine_process = Process(
      name="EngineProcess",
      target=Engine._engine_process_main,
      args=(caching_calculator, recv, queue_logger.queue),
    )
    engine_process.start()
    return cls(send, engine_process)

  def start_run_experiment(self, experiment: Experiment) -> int:
    """
    Request the engine to start asynchroously processing the specified
    Experiment.

    Returns the number of results the Experiment will produce. Returns
    0 if the Experiment could not be scheduled.
    """
    if not self._stream.send(experiment, blocking=False):
      return 0
    counter = 0
    for _, s in experiment.simulations():
      for reducer in s.get_reducers():
        counter += 1
    return counter

  def start_run_simulation(
    self, simulation: Simulation, key: VariantKey | None = None
  ) -> int:
    """
    Request the engine to start asynchroously processing the specified
    Simulation.

    Returns the number of results the Simulation will produce. Returns
    0 if the Simulation could not be scheduled.
    """
    if not self._stream.send((simulation, key or VariantKey()), blocking=False):
      return 0
    return len(simulation.get_reducers())

  def get_result(self, blocking: bool = False) -> ReducerResult | None:
    """
    Fetch result from the engine once it's calculated. This is non-blocking
    by default.
    """
    return self._stream.recv(blocking)

  def stop(self) -> None:
    self._stream.close()
    self._engine_process.join()

  def __del__(self) -> None:
    self.stop()

  @staticmethod
  def _engine_process_main(
    calculator: _CachingCalculator,
    stream: BidiStream,
    logging_queue: multiprocessing.Queue,
  ) -> None:
    # Fix logging
    bind_logging_to_queue(logging_queue)

    # Start the calculation
    logger.info(
      "Initializing Calculator: %s", type(calculator.result_calculator).__name__
    )
    calculator.initialize()
    while True:
      try:
        # Note: There is a deadlock here if we don't let an error computing
        # a result short-circuit the client
        command = stream.recv(blocking=True)
        if isinstance(command, Experiment):
          Engine._blocking_run_experiment(calculator, stream, command)
        elif isinstance(command, tuple) and isinstance(command[0], Simulation):
          Engine._run_simulation(calculator, stream, *command)
        else:
          logger.warning("Encountered unexpected command: %s. Skipping.", command)
      except EOFError:
        logger.debug("Received EOF. Ending EngineProcess")
        calculator.deinit()
        return
      except BaseException as e:
        logger.error("Encountered an exception: %s.", e)
        stream.send(e)
        return
      finally:
        stream.close()

  @staticmethod
  def _blocking_run_experiment(
    calculator: _CachingCalculator, stream: BidiStream, experiment: Experiment
  ) -> None:
    timer = Stopwatch()
    timer.start()
    num_simulations = 0
    computed_reducers = 0
    try:
      for bucket in Engine._get_simulations_grouped(experiment):
        for key, simulation in bucket:
          num_simulations += 1
          computed_reducers += Engine._run_simulation(
            calculator, stream, simulation, key, blocking=False,
          )
        computed = calculator.compute_reducers()
        for result in computed:
          stream.send(result, blocking=True)
    except Exception as e:
      logger.error("Encountered Error")
      raise e
    finally:
      timer.stop()
      logger.info(
        "Computed %d simulations (%d cache misses)",
        num_simulations,
        calculator.simulation_cache_misses,
      )
      logger.info(
        "Computed %d reducers (%d cache misses)",
        computed_reducers,
        computed_reducers - calculator.reducer_dups,
      )
      logger.info("Total Engine Elapsed Time: %ss", timer.total_elapsed_seconds())
      stream.close()

  @staticmethod
  def _run_simulation(
    calculator: _CachingCalculator,
    stream: BidiStream,
    simulation: Simulation,
    key: VariantKey,
    blocking: bool = True,
  ) -> int:
    calculator.raytrace(simulation)
    count = 0
    for reducer in simulation.get_reducers():
      count += 1
      calculator.schedule_reducer(reducer, ResultKey(reducer.name, key))
    if blocking:
      for result in calculator.compute_reducers():
        stream.send(result, blocking=True)
    return count

  @staticmethod
  def _get_simulations_grouped(
    experiment: Experiment,
  ) -> list[list[tuple[VariantKey, Simulation]]]:
    """
    Returns an iterator of Simulations, grouped by similarity such that
    similar simulations are always adjacent.

    Returns:
    + VariantKey - VariantKey for the Simulation
    + Simulation - The Simulation object
    + bool - If true, this is a new simulation that needs ray-traced.
    """
    buckets: list[list[tuple[VariantKey, Simulation]]] = []
    for variant, simulation in experiment.simulations():
      found_match = False
      for bucket in buckets:
        if bucket[-1][1].is_similar(simulation):
          found_match = True
          bucket.append((variant,simulation))
          break
      if not found_match:
        buckets.append([(variant, simulation)])
    return buckets
