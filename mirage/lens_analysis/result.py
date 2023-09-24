"""
Result Objects
==============

The `lens_analysis` module includes tools for handling the result of a calculation.

Under the hood, these classes are essentially thin wrappers around a `ResultFileManager`,
that orchestrates reading particular simulations / results in a structured manner.

The `MultiResult` is useful for comparing the results of multiple simulations. When analyzing
all the results from a singular `Simulation`, the `Result` object is most appropriate.


By default, the loaders must support multiple Simulations in one file. Thus, a `MultiResult`
is returned. If you know your result file includes only one simulation, you can unpack it to the
`Result` object by calling .get_result() on the returned MultiResult.
"""
from typing import Optional, Any, List
from dataclasses import dataclass
from functools import cached_property

from mirage.util.io import ResultFileManager
from mirage.calc import Reducer
from mirage.sim import Simulation, SimulationBatch


@dataclass
class Result:
  io_manager: ResultFileManager
  simulation_id: int

  @cached_property
  def simulation(self) -> Simulation:
    return self.io_manager.load_simulation()[self.simulation_id]

  @property
  def reducer_names(self) -> list[str]:
    return [r.name for r in self.simulation.reducers]

  def get_reducer(self, name: str) -> Reducer:
    for reducer in self.simulation.reducers:
      if reducer.name == name:
        return reducer
    raise ValueError(f"Could not find reducer with name '{name}'")


class MultiResult:

  def __init__(self, filename: str):
    self._io: ResultFileManager = ResultFileManager.new_loader(filename)

  @cached_property
  def simulation_batch(self) -> SimulationBatch:
    return self._io.load_simulation()

  def get_result(self, index: int = 0) -> Result:
    if index >= len(self._io):
      raise ValueError(
        f"Cannot extract Simulation {index} from file containing {len(self._io)} simulations")
    return Result(self._io, index)

  def simulation(self, index: int = 0) -> Simulation:
    return self.simulation_batch[index]

  def get_reducers_by_name(self, name: str) -> list[Reducer]:
    reducers = []
    for i in range(len(self)):
      try:
        reducers.append(self.get_result(i).get_reducer(name))
      except ValueError:
        raise ValueError(
          f"Could not find Reducer with name '{name}' in Simulation with index={i}")
    return reducers

  def __len__(self) -> int:
    return len(self.simulation_batch)
