"""
Result Objects
==============

The `lens_analysis` module includes tools for handling the result of a
calculation. Under the hood, these classes are essentially thin wrappers around
a `ResultFileManager`, that orchestrates reading particular simulations /
results in a structured manner.

The `MultiResult` is useful for comparing the results of multiple simulations.
When analyzing all the results from a singular `Simulation`, the `Result`
object is most appropriate.


By default, the loaders must support multiple Simulations in one file. Thus, a
`MultiResult` is returned. If you know your result file includes only one
simulation, you can unpack it to the `Result` object by calling .get_result()
on the returned MultiResult.
"""

from dataclasses import dataclass
from functools import cached_property
from typing import Iterator

from mirage.io import ResultFileManager
from mirage.calc import Reducer
from mirage.sim import Simulation, Experiment
from mirage.util import VariantKey


@dataclass
class SimulationResult:
  """
  Provides an interface for analyzing the results of one single Simulation.
  """

  experiment: Experiment
  io_manager: ResultFileManager
  variant_key: VariantKey

  @cached_property
  def simulation(self) -> Simulation:
    return self.experiment.get(self.variant_key)

  @property
  def reducer_names(self) -> list[str]:
    return [r.name for r in self.simulation.reducers]

  def get_reducer(self, name: str) -> Reducer:
    return self.io_manager.load_result(name, self.variant_key)

  def __len__(self) -> int:
    return len(self.reducer_names)

  def __iter__(self) -> Iterator[Reducer]:
    return iter([self.get_reducer(name) for name in self.reducer_names])


@dataclass
class ExperimentResult:
  """
  Provides an interface for analyzing Experiment results.

  Wraps a ResultFileManager and manages lazily loading results.
  """

  io_manager: ResultFileManager

  @cached_property
  def experiment(self) -> Experiment:
    return self.io_manager.load_experiment()

  @property
  def keys(self) -> list[VariantKey]:
    return self.experiment.variant_keys

  def simulation(self, key: VariantKey) -> SimulationResult:
    if self.experiment.get(key) is None:
      raise KeyError(f"Unrecognized key: {key}")
    return SimulationResult(self.experiment, self.io_manager, key)

  def __len__(self) -> int:
    return len(self.experiment)

  def __iter__(self) -> Iterator[SimulationResult]:
    return iter([self.simulation(k) for k in self.keys])


@dataclass
class InMemorySimulationResult:
  """
  Implements the SimulationResult interface without any underlying File I/O,
  reading from in-memory datastructures.
  """

  simulation: Simulation
  reducers: dict[str, Reducer]

  @property
  def reducer_names(self) -> list[str]:
    return list(self.reducers.keys())

  def get_reducer(self, name: str) -> Reducer:
    return self.reducers[name]

  def __len__(self) -> int:
    return len(self.reducers)

  def __iter__(self) -> Iterator[Reducer]:
    return iter(self.reducers.values())
