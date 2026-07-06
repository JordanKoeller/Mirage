from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from astropy import units as u

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.patches import Ellipse
from matplotlib.widgets import AxesWidget, Button, CheckButtons
import numpy as np

from mirage.viz.window import VizWindow, MirageAxes
from mirage.calc.reducers import LensedImageReducer
from mirage.calc.reducer_funcs import draw_lensed_image
from mirage.viz.viz_state import VizState, VizEvent, Panel
from mirage.viz.controller import Controller
from mirage.util import Index2D, VariantKey, Vec2D, LabeledStopwatch

_COLOR_PALETTE = {
    "POS_PARITY_START": np.array([245, 0, 66], dtype=np.float64),
    "POS_PARITY_STOP": np.array([245, 162, 184], dtype=np.float64),
    "NEG_PARITY_START": np.array([4, 136, 217], dtype=np.float64),
    "NEG_PARITY_STOP": np.array([89, 187, 247], dtype=np.float64),
    "QSO": np.array([107, 103, 219], dtype=np.uint8),
    "BACKGROUND": np.array([0, 0, 0], dtype=np.uint8),
}

_RENDER_QSO = "Render Quasar"

class LensedImageController(Controller):
    def __init__(self, reducer_name: str | None = None) -> None:
        Controller.__init__(self)
        self._reducer_name = reducer_name
        self.reset()

    @property
    def supported_reducers(self) -> list[type[Reducer]]:
        return [LensedImageReducer]

    def reset(self) -> None:
        self._frame = 0
        self._draw_qso = False
        self._canvas = None
        self._img = None
        self._lightcurve = None
        self._lightcurve_plot = None
        self._lightcurve_marker = None
        self._normalization_factor = 0
        self._active_ind = 0
        self._render_controls = {
            _RENDER_QSO: False,
        }
        self.request_draw()

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        reducer = self.find_reducer(state, LensedImageReducer, reducer_name = self._reducer_name)
        artists = []
        data = []
        for i, vk in enumerate(state.variant_keys):
            output = self.find_reducer(state, LensedImageReducer, variant_key=vk).output
            data.append(output)
            self._normalization_factor = max(np.max(np.abs(reducer.output)), self._normalization_factor)
            if vk == state.variant_key:
                self._active_ind = i
        artists.append(self._draw_lensed_image(reducer.output, state, window))
        artists.extend(self._draw_light_curve(data, reducer.unlensed_pixel_count, window))
        artists.extend(self._draw_light_curve_marker(window))
        return artists

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        axes.set_axis_on()
        buttons = CheckButtons(
            axes,
            labels=[
                _RENDER_QSO,
            ],
            actives=[
                self._render_controls[_RENDER_QSO],
            ]
        )
        buttons.on_clicked(self._on_button_pressed)
        return [buttons]

    def on_event(self, state: VizState, event: VizEvent) -> bool:
        pass

    def _draw_lensed_image(self, img: np.ndarray, state: VizState, window: VizWindow) -> list[Artist]:
        if self._canvas is None:
            self._canvas = np.ndarray((*img.shape, 3), dtype=np.uint8)
        draw_lensed_image(self._canvas, img, _COLOR_PALETTE, self._normalization_factor - 1)

        tl, br = state.lens_region.to("uas").span
        if self._img is None:
            self._img = window.im_axes.imshow(
                self._canvas,
                extent=(
                    tl.x.value, # left
                    br.x.value, # right
                    br.y.value, # bottom
                    tl.y.value, # top
                ),
            )
        else:
            self._img.set(array=self._canvas)
        return [self._img]

    def _draw_light_curve(self, data: list[np.ndarray], unlensed_pixel_count: int, window: VizWindow) -> list[Artist]:
        if self._lightcurve is None:
            self._lightcurve = np.array([ -2.5 * np.log10(np.sum(d) / unlensed_pixel_count)  for d in data])
        if self._lightcurve_plot:
            self._lightcurve_plot.set_data([i for i in range(len(self._lightcurve))], self._lightcurve)
        else:
            self._lightcurve_plot = window.line_axes.plot(self._lightcurve)[0]
        return [self._lightcurve_plot]

    def _draw_light_curve_marker(self, window: VizWindow) -> list[Artist]:
        view_ratio = 3
        w = len(self._lightcurve) * 0.02 / view_ratio
        h = abs((np.max(self._lightcurve) - np.min(self._lightcurve))) * 0.02 * view_ratio
        cx = self._active_ind
        cy = self._lightcurve[self._active_ind]
        if not self._lightcurve_marker:
            self._lightcurve_marker = Ellipse((cx, cy), width=w, height=h)
            window.line_axes.add_artist(self._lightcurve_marker)
        else:
            self._lightcurve_marker.set(center=(cx,cy), width=w, height=h)
        return [self._lightcurve_marker]

    def _on_button_pressed(self, label, *args, **kwargs) -> None:
        self._render_controls[label] = not self._render_controls[label]
        self.request_draw()


