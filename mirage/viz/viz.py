from abc import ABC, abstractmethod
from typing import Type, List

from matplotlib.axes import Axes

from mirage.lens_analysis.result import ExperimentResult, SimulationResult
from mirage.calc import Reducer

class Viz(ABC):
    __registry: List[type] = []

    def bind_experiment(self, experiment: ExperimentResult) -> None:
        self._experiment = experiment
        self._simulation_id = 0

    def bind_window(self, callback: callable) -> None:
        """
        Binds self to a VizWindow instance.
        """
        self._request_draw_callback = callback

    def to_next_simulation(self) -> bool:
        """
        Advance to the next simulation in the experiment.

        Returns a boolean, indicating if there are any more simulations to
        advance to.
        """
        if self._experiment and self._simulation_id < len(self._experiment):
            self._simulation_id += 1
        return self._simulation_id < len(self._experiment)

    def to_prev_simulation(self) -> bool:
        """
        Go back a simulation.

        Returns a boolean, indicating if the active simulation is the 0'th
        simulation
        """
        if self._experiment and self._simulation_id > 0:
            self._simulation_id -= 1
        return not self._simulation_id == 0

    def defer_draw(self) -> None:
        """
        Request for a re-draw of the visualizer.

        Note that this method does not guarantee that a draw will occur, but
        notifies the visualizer that a new frame is ready. It is ultimately up
        to the `VizWindow` to decide if a frame draw will be done.
        """
        self._request_draw_callback()

    @property
    def simulation(self) -> SimulationResult:
        return self._experiment.get_result(self._simulation_id)

    @abstractmethod
    def draw(self, canvas: Axes, line_graph: Axes) -> None:
        """
        Draw the visualizer to the provided axes.
        """

    @classmethod
    @abstractmethod
    def compatible_reducers(cls) -> List[Type[Reducer]]:
        """
        Returns the list of reducers that can be visualized by this visualizer
        """

    @staticmethod
    def register(klass):
        if not issubclass(klass, Viz):
            raise ValueError("Visualizers must be a subclass of mirage.viz.Viz")
        Viz.__registry.append(klass)
        return klass

    @staticmethod
    def get_visualizers() -> List['Viz']:
        return Viz.__registry

    def get_event_handlers(self) -> dict[str, callable]:
        return {}
