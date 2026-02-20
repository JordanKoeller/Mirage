from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from astropy import units as u

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
from mirage.viz.controller import Controller
from mirage.util import Index2D, VariantKey, Vec2D

class MagMapController(Controller):
    @dataclass
    class _LineState:
        start_x: float
        start_y: float
        dragging: bool
        end_x: float
        end_y: float
        unit: u.Unit

    def __init__(self, reducer_name: str | None = None) -> None:
        Controller.__init__(self)
        self._reducer_name = reducer_name
        self.reset()

    @property
    def supported_reducers(self) -> list[type[Reducer]]:
        return [MagnificationMapReducer]

    def reset(self) -> None:
        self._line_state: self._LineState | None = None
        self._line: Line2D | None = None
        self._colorbar = None
        self._img = None
        self._show_all_lines = False
        self._legend = None
        self._lightcurves: dict[str, Artist] = {}
        self.request_draw()

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        reducer = self.find_reducer(state, MagnificationMapReducer, reducer_name = self._reducer_name)
        magnitudes = reducer.magnitudes
        artists = []

        colormap = plt.get_cmap("RdBu")

        tl, br = reducer.source_region.to("uas").span
        if self._img is None:
            self._img = window.im_axes.imshow(
                magnitudes,
                norm=colors.TwoSlopeNorm(vcenter=0.0),
                cmap=colormap,
                extent=(
                    tl.x.value, # left
                    br.x.value, # right
                    br.y.value, # bottom
                    tl.y.value, # top
                ),
            )
        else:
            self._img.set(array=magnitudes)
        self.request_bounds(MirageAxes.IMAGE, tl.x.value, br.x.value, br.y.value, tl.y.value)
        artists.append(self._img)

        if self._colorbar is None:
            self._colorbar = window.figure.colorbar(
                self._img, ax=window.im_axes, pad=0.01, fraction=0.05,
                location="bottom",
            )
            self._colorbar.set_label("Magnitudes")
        else:
            self._colorbar.update_normal()

        artists.extend(self._get_line_artist(window))
        legend_handles = []
        for ind, variant_key in enumerate(state.variant_keys):
            if not self._show_all_lines and state.variant_key != variant_key:
                lightcurve = self._hide_lightcurve_artist(variant_key)
                if lightcurve:
                    artists.append(lightcurve)
                continue
            was_drawn = self._draw_lightcurve_artist(
                ind, 
                variant_key,
                ind == state.variant_key_index,
                self.find_reducer(state, MagnificationMapReducer, variant_key=variant_key),
                window)
            if was_drawn:
                artists.append(self._lightcurves[variant_key])
                legend_handles.append(self._lightcurves[variant_key])
        self._legend = window.line_axes.legend(handles=list(legend_handles), loc="upper right")
        artists.append(self._legend)

        return artists

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        axes.set_axis_on()
        button = Button(axes, "Show All")
        button.on_clicked(lambda *args: self._toggle_show_all())
        return [
            button,
        ]

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
                unit=state.source_region.unit,
            )
            self.request_draw()
            return True
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
                unit=self._line_state.unit,
            )
            self.request_draw()
            return True
        if event.name == "button_release_event" and self._line_state:
            self._line_state = self._LineState(
                start_x=self._line_state.start_x,
                start_y=self._line_state.start_y,
                dragging=False,
                end_x=self._line_state.end_x,
                end_y=self._line_state.end_y,
                unit=self._line_state.unit,
            )
            self.request_draw()
            return True
        return False, False


    def _get_line_artist(self, window: VizWindow) -> Iterable[Artist]:
        artists = []
        if self._line_state is None:
            return artists
        if self._line is None:
            self._line = Line2D(
                [self._line_state.start_x.value, self._line_state.end_x.value],
                [self._line_state.start_y.value, self._line_state.end_y.value],
                linewidth=3,
            )
            window.im_axes.add_line(self._line)
        else:
            self._line.set(
                xdata=[self._line_state.start_x.value, self._line_state.end_x.value],
                ydata=[self._line_state.start_y.value, self._line_state.end_y.value],
            )
        artists.append(self._line)
        return artists

    def _hide_lightcurve_artist(
        self,
        variant_key: VariantKey,
    ) -> Artist | None:
        """Hide the specified lightcurve from the plot."""
        if variant_key not in self._lightcurves:
            return None
        artist = self._lightcurves[variant_key]
        artist.set_visible(False)
        return artist
    
    def _draw_lightcurve_artist(
        self,
        ind: int,
        variant_key: VariantKey,
        primary: bool,
        reducer: MagnificationMapReducer,
        window: VizWindow
    ) -> bool:
        """
        Renders a lightcurve to the window.line_axes, returning a boolean if a line was drawn or not.
        """
        slice_x = []
        slice_y = []
        unit = ""
        if self._line_state and not self._line_state.dragging:
            slice_x, slice_y = reducer.slice(
                Vec2D(self._line_state.start_x.value, self._line_state.start_y.value, self._line_state.unit),
                Vec2D(self._line_state.end_x.value, self._line_state.end_y.value, self._line_state.unit),
            )
            unit = str(slice_x.unit)
            slice_x = slice_x.value
        if variant_key not in self._lightcurves:
            self._lightcurves[variant_key] = window.line_axes.plot(
                slice_x,
                slice_y,
                label=str(variant_key),
                alpha=1.0 if primary else 0.25)[0]
            window.line_axes.set_xlabel(unit)
            window.line_axes.set_ylabel("Magnitudes")
        else:
            self._lightcurves[variant_key].set_data(
                    slice_x,
                    slice_y,
            )
            self._lightcurves[variant_key].set_visible(True)
            self._lightcurves[variant_key].set_alpha(1.0 if primary else 0.25)
        if len(slice_x) == 0:
            return False
        self.request_bounds(MirageAxes.LINE, 0, slice_x[-1], np.min(slice_y), np.max(slice_y))
        return True

    def _toggle_show_all(self) -> None:
        self._show_all_lines = not self._show_all_lines
        self.request_draw()

