from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from matplotlib.axes import Axes
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors
from matplotlib.artist import Artist
import numpy as np

from mirage.viz.window import VizWindow
from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz.viz_state import VizState, VizEvent, Panel

class Controller(ABC):

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

        If the event should not propagate to other layers, return True. Otherwise,
        return False (or None).
        """
        return False


class MagMapController(Controller):
    @dataclass
    class _LineState:
        start_x: int
        start_y: int
        dragging: bool
        end_x: int
        end_y: int

    def __init__(self, reducer_name: str | None = None) -> None:
        self._reducer_name = reducer_name
        self.reset()

    def reset(self) -> None:
        self._line_state: _LineState | None = None
        self._line: Line2D | None = None
        self._colorbar = None
        self._img = None

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        reducer = self._find_reducer(state)
        magnitudes = reducer.magnitudes
        artists = []

        colormap = plt.get_cmap("RdBu")

        if self._img is None:
            self._img = window.im_axes.pcolormesh(
                magnitudes,
                norm=colors.TwoSlopeNorm(vcenter=0.0),
                cmap=colormap)
        else:
            self._img.set(array=magnitudes)
        artists.append(self._img)

        if self._colorbar is None:
            self._colorbar = window.figure.colorbar(
                self._img, ax=window.im_axes, pad=0.01, fraction=0.05)
            self._colorbar.set_label("Magnitudes")
        else:
            self._colorbar.update_normal()

        if self._line_state:
            if self._line is None:
                self._line = Line2D(
                    [self._line_state.start_x, self._line_state.end_x],
                    [self._line_state.start_y, self._line_state.end_y],
                    linewidth=3,
                )
                window.im_axes.add_line(self._line)
            else:
                self._line.set(
                    xdata=[self._line_state.start_x, self._line_state.end_x],
                    ydata=[self._line_state.start_y, self._line_state.end_y],
                )
            artists.append(self._line)
        return artists


    def on_event(self, state: VizState, event: VizEvent) -> bool:
        if event.panel != Panel.IMAGE:
            return False
        if event.name == "button_press_event":
            self._line_state = self._LineState(
                start_x=event.screen_pos.x,
                start_y=event.screen_pos.y,
                dragging=True,
                end_x=event.screen_pos.x,
                end_y=event.screen_pos.y,
            )
        if event.name == "motion_notify_event" and self._line_state and self._line_state.dragging:
            self._line_state = self._LineState(
                start_x=self._line_state.start_x,
                start_y=self._line_state.start_y,
                dragging=self._line_state.dragging,
                end_x=event.screen_pos.x,
                end_y=event.screen_pos.y,
            )
        if event.name == "button_release_event" and self._line_state:
            self._line_state = self._LineState(
                start_x=self._line_state.start_x,
                start_y=self._line_state.start_y,
                dragging=False,
                end_x=self._line_state.end_x,
                end_y=self._line_state.end_y,
            )



    def _find_reducer(self, state: VizState) -> MagnificationMapReducer:
        if self._reducer_name:
            for reducer in state.simulation_result:
                if self._reducer_name == reducer.name:
                    return reducer
            raise ValueError(f"Could not find reducer with name {self._reducer_name}")
        reducers = []
        for reducer in state.simulation_result:
            if isinstance(reducer, MagnificationMapReducer):
                reducers.append(reducer)
        if len(reducers) == 0:
            raise ValueError("Could not find a MagnificationMapReducer")
        if len(reducers) > 1:
            raise ValueError(f"Ambiguous MagnificationMapReducers: {', '.join(reducer.name for reducer in reducers)}")
        return reducers[0]



