from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget, Button
import numpy as np

from mirage.viz.window import VizWindow, MirageAxes
from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz.viz_state import VizState, VizEvent, Panel
from mirage.util import Index2D, VariantKey


@dataclass
class AxesBounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def update(self, x_min: float, x_max: float, y_min: float, y_max: float) -> None:
        self.x_min = min(self.x_min, x_min)
        self.x_max = max(self.x_max, x_max)
        self.y_min = min(self.y_min, y_min)
        self.y_max = max(self.y_max, y_max)

    def merge(self, other: "AxesBounds") -> None:
        self.update(other.x_min, other.x_max, other.y_min, other.y_max)


class Controller(ABC):
    def __init__(self) -> None:
        self.__stale = True
        self.__bounds = {axis: None for axis in MirageAxes}

    def request_draw(self) -> None:
        """
        Request Viz to redraw the UI for this controller. This method should
        be called after any state change that means the current rendered UI
        is stale and needs refreshed. Once called the UI loop will redraw this
        controller on the next iteration.

        Note that the controller may be drawn even if this method has not been
        called.
        """
        self.__stale = True

    def do_draw(
        self, state: VizState, window: VizWindow, force: bool = False
    ) -> tuple[bool, Iterable[Artist]]:
        """
        Method called by the render loop to draw this controller.

        This method SHOULD NOT be overriden by subclasses. Overrides should happen
        on the "draw()" method instead.

        Returns:
          did_draw (bool) - Indicates if a draw happened, or if it was skipped.
          artists (Iterable[Artist]) - Artists to draw for this controller.
        """
        if not force and not self.__stale:
            return False, []
        self.__stale = False
        self.__bounds = {axis: None for axis in MirageAxes}
        return True, self.draw(state, window)

    @property
    @abstractmethod
    def supported_reducers(self) -> list[type[Reducer]]:
        """
        Return the types of Reducers that this Controller can visualize.

        If the Controller supports all reducers, an empty list should be
        returned.
        """

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the Controller to its initial state.
        """

    @abstractmethod
    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        """
        Draw the controller to the specified axes.

        This method should NOT clear the axes as that would remove anything drawn
        by other controllers. It should draw a completely new frame each time `draw`
        is called. The Axes are cleared between each call to draw()
        """

    def on_event(self, state: VizState, event: VizEvent) -> bool:
        """
        Intercept a UI event.


        Returns a booleans indicating if the event should be consumed
        or continue propagating to more layers.
        """
        return False

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        """
        Create and attach any widgets associate with the Controller to the
        specified Axes.

        Returns any created axes in a list.
        """
        return []

    def request_bounds(
        self, axis: MirageAxes, x_min: float, x_max: float, y_min: float, y_max: float
    ) -> None:
        """
        Request the specified MirageAxes have its bounds set to the provided
        values.

        Note that the requested bounds may not be respected if other Controllers
        require a larger bounds.
        """
        if self.__bounds[axis] is None:
            self.__bounds[axis] = AxesBounds(x_min, x_max, y_min, y_max)
        else:
            self.__bounds[axis].update(x_min, x_max, y_min, y_max)

    def find_reducer(
        self,
        state: VizState,
        reducer_type: object,
        variant_key: VariantKey | None = None,
        reducer_name: str | None = None,
    ) -> Reducer | None:
        """
        Returns the first reducer that:
        + Comes from the Simulation matching the variant_key. If not provided,
          the active variant in the VizState is used.
        + Matches the reducer_name (if specified).
        + Is a reducer of the specified reducer_type.

        If no such reducer exists (or multiple matches are found), None is returned

        TODO: Refactor this to support RealtimeVizState.
        """
        simulation = state.simulation_result(variant_key)
        if reducer_name:
            return simulation.get_reducer(reducer_name)
        reducers = []
        for reducer in simulation:
            if isinstance(reducer, reducer_type):
                reducers.append(reducer)
        if len(reducers) == 0:
            # raise ValueError(f"Could not find a reducer with type {reducer_type.__name__}")
            return None
        if len(reducers) > 1:
            return None
            # raise ValueError(
            #     f"Ambiguous {reducer_type.__name__}'s: {', '.join(reducer.name for reducer in reducers)}"
            # )
        return reducers[0]

    @property
    def _bounds(self) -> dict[MirageAxes, AxesBounds]:
        return self.__bounds
