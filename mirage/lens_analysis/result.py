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

from mirage.io import ResultFileManager
from mirage.calc import Reducer
from mirage.sim import Simulation, Experiment


@dataclass
class SimulationResult:
    io_manager: ResultFileManager
    simulation_id: int

    @cached_property
    def simulation(self) -> Simulation:
        return self.io_manager.load_simulation()[self.simulation_id]

    @property
    def reducer_names(self) -> list[str]:
        return [r.name for r in self.simulation.reducers]

    def get_reducer(self, name: str) -> Reducer:
        return self.io_manager.load_result(name, self.simulation_id)


@dataclass
class ExperimentResult:
    io_manager: ResultFileManager

    @cached_property
    def simulation_batch(self) -> Experiment:
        return self.io_manager.load_simulation()

    def get_result(self, index: int = 0) -> SimulationResult:
        if index >= len(self):
            raise ValueError(
                f"Cannot extract Simulation {index} from file containing "
                f"{len(self.io_manager)} simulations"
            )
        return SimulationResult(self.io_manager, index)

    def simulation(self, index: int = 0) -> Simulation:
        return self.simulation_batch[index]

    def get_reducers_by_name(self, name: str) -> list[Reducer]:
        reducers = []
        for i in range(len(self)):
            try:
                reducers.append(self.get_result(i).get_reducer(name))
            except ValueError:
                raise ValueError(
                    f"Could not find Reducer with name '{name}' in Simulation "
                    f"with index={i}"
                )
        return reducers

    def __len__(self) -> int:
        return len(self.simulation_batch)
