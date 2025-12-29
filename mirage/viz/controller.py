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

from mirage.viz.window import VizWindow
from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz.viz_state import VizState, VizEvent, Panel
from mirage.util import Index2D, VariantKey


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

    def on_event(self, state: VizState, event: VizEvent) -> tuple[bool, bool]:
        """
        Intercept a UI event.


        Returns a tuple of booleans:
          + The first boolean indicates if the event should be consumed. Consumed
            events do not propagate to more layers.
          + The second boolean indicates if the layer should be redrawn. 
        """
        return False, False

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        """
        Create and attach any widgets associate with the Controller to the
        specified Axes.

        Returns any created axes in a list.
        """
        return []


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
        self._line_state: self._LineState | None = None
        self._line: Line2D | None = None
        self._colorbar = None
        self._img = None
        self._lightcurves = []
        self._show_all_lines = False
        self._legend = None

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        reducer = self._find_reducer(state)
        magnitudes = reducer.magnitudes
        artists = []

        colormap = plt.get_cmap("RdBu")

        if self._img is None:
            self._img = window.im_axes.pcolormesh(
                magnitudes, norm=colors.TwoSlopeNorm(vcenter=0.0), cmap=colormap
            )
        else:
            self._img.set(array=magnitudes)
        artists.append(self._img)

        if self._colorbar is None:
            self._colorbar = window.figure.colorbar(
                self._img, ax=window.im_axes, pad=0.01, fraction=0.05
            )
            self._colorbar.set_label("Magnitudes")
        else:
            self._colorbar.update_normal()

        window.line_axes.set_xlim(0, 0.1)
        window.line_axes.set_ylim(0.5, -0.5)
        artists.extend(self._get_line_artist(window))
        if self._line_state and self._line_state.dragging:
            return artists
        if self._show_all_lines:
            for ind, variant_key in enumerate(state.variant_keys):
                artists.extend(self._get_lightcurve_artist(
                    ind, 
                    variant_key,
                    ind == state.variant_key_index,
                    self._find_reducer(state, variant_key),
                    window))
        else:
            artists.extend(self._get_lightcurve_artist(0, state.variant_key, True, reducer, window))
        self._legend = window.line_axes.legend(loc="upper right")

        return artists

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        axes.set_axis_on()
        button = Button(axes, "Show All")
        button.on_clicked(lambda *args: self._toggle_show_all())
        return [
            button,
        ]

    def on_event(self, state: VizState, event: VizEvent) -> tuple[bool, bool]:
        if event.panel != Panel.IMAGE:
            return False, False
        if event.name == "button_press_event":
            self._line_state = self._LineState(
                start_x=event.screen_pos.x,
                start_y=event.screen_pos.y,
                dragging=True,
                end_x=event.screen_pos.x,
                end_y=event.screen_pos.y,
            )
            return True, True
        if (
            event.name == "motion_notify_event"
            and self._line_state
            and self._line_state.dragging
        ):
            self._line_state = self._LineState(
                start_x=self._line_state.start_x,
                start_y=self._line_state.start_y,
                dragging=self._line_state.dragging,
                end_x=event.screen_pos.x,
                end_y=event.screen_pos.y,
            )
            return True, True
        if event.name == "button_release_event" and self._line_state:
            self._line_state = self._LineState(
                start_x=self._line_state.start_x,
                start_y=self._line_state.start_y,
                dragging=False,
                end_x=self._line_state.end_x,
                end_y=self._line_state.end_y,
            )
            return True, True
        return False, False

    def _find_reducer(
        self, state: VizState,
        variant_key: VariantKey | None = None,
    ) -> MagnificationMapReducer:
        simulation = state.simulation_result
        if variant_key:
            simulation = state.experiment.simulation(variant_key)
        if self._reducer_name:
            return simulation.get_reducer(self._reducer_name)
        reducers = []
        for reducer in simulation:
            if isinstance(reducer, MagnificationMapReducer):
                reducers.append(reducer)
        if len(reducers) == 0:
            raise ValueError("Could not find a MagnificationMapReducer")
        if len(reducers) > 1:
            raise ValueError(
                f"Ambiguous MagnificationMapReducers: {', '.join(reducer.name for reducer in reducers)}"
            )
        return reducers[0]

    def _get_line_artist(self, window: VizWindow) -> Iterable[Artist]:
        artists = []
        if self._line_state is None:
            return artists
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
    
    def _get_lightcurve_artist(self, ind: int, variant_key: VariantKey, primary: bool, reducer: MagnificationMapReducer, window: VizWindow) -> Iterable[Artist]:
        artists = []
        if self._line_state is None:
            return artists
        slice_x, slice_y = reducer.slice(
            Index2D(self._line_state.start_x, self._line_state.start_y),
            Index2D(self._line_state.end_x, self._line_state.end_y),
        )
        if len(slice_x) == 0:
            return artists

        if len(self._lightcurves) <= ind:
            self._lightcurves.append(window.line_axes.plot(
                slice_x.value,
                slice_y,
                label=str(variant_key),
                alpha=1.0 if primary else 0.25)[0])
            window.line_axes.set_xlabel(str(slice_x.unit))
            window.line_axes.set_ylabel("Magnitudes")
        else:
            self._lightcurves[ind].set_data(
                    slice_x.value,
                    slice_y,
            )
            self._lightcurves[ind].set_alpha(1.0 if primary else 0.25)
        window.line_axes.set_xlim(
            0,
            max(slice_x.value[-1], window.line_axes.get_xlim()[1]))
        window.line_axes.set_ylim(
            max(np.max(slice_y), window.line_axes.get_ylim()[0]),
            min(np.min(slice_y), window.line_axes.get_ylim()[1]))
        artists.append(self._lightcurves[ind])
        return artists

    def _toggle_show_all(self) -> None:
        self._show_all_lines = not self._show_all_lines

