from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Iterator
import logging
from multiprocessing import Process

from mirage.sim import Simulation, Experiment
from mirage.calc import Reducer, KdTree
from mirage.util import BidiStream, RepeatLogger, Stopwatch, VariantKey

logger = logging.getLogger(__name__)

_STREAM_BUFFER_SZ = 4



@dataclass
class ResultEvent:
    result: object
    simulation_key: VariantKey

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
    def apply_reducer(self, simulation: Simulation, reducer: Reducer) -> Reducer:
        """
        Apply the specified reducer and return a reference to the hydrated
        version. This may or mahy not be the same instance as what was passed in.
        """

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
    def create_and_start(cls, calculator: ResultCalculator) -> Self:
        send, recv = BidiStream.create(_STREAM_BUFFER_SZ)
        engine_process = Process(
            name="EngineProcess",
            target=Engine._engine_process_main,
            args=(calculator, recv)
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
    
    def start_run_simulation(self, simulation: Simulation, key: VariantKey | None = None) -> int:
        """
        Request the engine to start asynchroously processing the specified
        Simulation.

        Returns the number of results the Simulation will produce. Returns
        0 if the Simulation could not be scheduled.
        """
        if not self._stream.send((simulation, key or VariantKey()), blocking=False):
            return 0
        counter = 0
        return len(simulation.get_reducers())

    def get_result(self, blocking: bool = False) -> ResultEvent | None:
        """
        Fetch result from the engine once it's calculated. This is non-blocking
        by default.
        """
        return self._stream.recv(blocking)

    def __del__(self) -> None:
        self._stream.close()
        self._engine_process.join()


    @staticmethod
    def _engine_process_main(calculator: ResultCalculator, stream: BidiStream) -> None:
        logger.info(f"Initializing Calculator: %s", calculator)
        calculator.initialize()
        while True:
            try:
                # Note: There is a deadlock here if we don't let an error computing
                # a result short-circuit the client
                command = stream.recv(blocking=True)
                if isinstance(command, Experiment):
                    Engine._blocking_run_experiment(calculator, stream, command)
                elif isinstance(command, tuple) and isinstance(command[0], Simulation):
                    Engine._blocking_run_simulation(calculator, stream, *command)
                else:
                    logger.warning("Encountered unexpected command: %s. Skipping.", command)
            except EOFError:
                logger.info("Received EOF. Ending EngineProcess")
                return
            except BaseException as e:
                logger.error(f"Encountered an exception: %s.", s)
                stream.send(e)
                return
            finally:
                stream.close()


    @staticmethod
    def _blocking_run_experiment(
        calculator: ResultCalculator,
        stream: BidiStream,
        experiment: Experiment
    ) -> None:
        timer = Stopwatch()
        timer.start()
        num_simulations = 0
        cache_misses =  -1 # We don't call the first simulation a cache miss.
        try:
            for key, simulation, needs_traced in Engine._get_simulations_grouped(experiment):
                num_simulations += 1
                if needs_traced:
                    cache_misses += 1
                    calculator.raytrace(simulation)
                Engine._blocking_run_simulation(calculator, stream, simulation, key)
        except Exception as e:
            logger.error("Encountered Error")
            logger.error(str(e))
        finally:
            timer.stop()
            logger.info(
                "Computed %d simulations (%d cache misses)", num_simulations, cache_misses
            )
            logger.info(
                "Total Engine Elapsed Time: %ss", timer.total_elapsed_seconds()
            )
            stream.close()

    @staticmethod
    def _blocking_run_simulation(
        calculator: ResultCalculator,
        stream: BidiStream,
        simulation: Simulation,
        key: VariantKey,
    ):
        for reducer in simulation.get_reducers():
            result = calculator.apply_reducer(simulation, reducer)
            stream.send(ResultEvent(result, key), blocking=True)
        
    @staticmethod
    def _get_simulations_grouped(experiment: Experiment) -> Iterator[tuple[VariantKey, Simulation, bool]]:
        """
        Returns an iterator of Simulations, grouped by similarity such that
        similar simulations are always adjacent.

        Returns:
        + VariantKey - VariantKey for the Simulation
        + Simulation - The Simulation object
        + bool - If true, this is a new simulation that needs ray-traced.
        """
        buckets: list[tuple[VariantKey, Simulation]] = []
        for simulation in experiment.simulations():
            found_match = False
            for bucket in buckets:
                if bucket[-1][1].is_similar(simulation[1]):
                    found_match = True
                    bucket.append(simulation)
                    break
            if not found_match:
                buckets.append([simulation])
        for bucket in buckets:
            first_in_bucket = True
            for simulation in bucket:
                yield (*simulation, first_in_bucket)
                first_in_bucket = False
