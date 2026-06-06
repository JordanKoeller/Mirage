import numpy as np

from matplotlib.lines import Line2D
from matplotlib.widgets import AxesWidget, Button
from matplotlib.artist import Artist
from matplotlib.axes import Axes

from mirage.viz.window import VizWindow, MirageAxes
from mirage.calc.reducers import LightCurvesReducer
from mirage.viz.controller import Controller
from mirage.viz.viz_state import VizState, VizEvent, Panel

_NON_SELECTED_COLOR = 'b'
_SELECTED_COLOR = 'g'

class LightcurvesController(Controller):

    def __init__(self, reducer_name: str | None = None) -> None:
        Controller.__init__(self)
        self._reducer_name = reducer_name
        self.reset()

    @property
    def supported_reducers(self) -> list[type[Reducer]]:
        return [LightCurvesReducer]

    def reset(self) -> None:
        self._lines: list[Line2D] = []
        self._lightcurves: dict[str, Artist] = {}
        self._selected_line = -1 # index in self._lines of selected line
        self._show_all_lines = False

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        artists = []
        try:
            reducer = self.find_reducer(state, LightCurvesReducer, self._reducer_name)
        except ValueError:
            return artists
        tl, br = state.source_region.to("uas").span
        self.request_bounds(MirageAxes.IMAGE, tl.x.value, br.x.value, br.y.value, tl.y.value)
        if len(self._lines) == 0:
            for lightcurve in reducer.lightcurves:
                line = Line2D(
                    [lightcurve.start_pos.x.value, lightcurve.end_pos.x.value],
                    [lightcurve.start_pos.y.value, lightcurve.end_pos.y.value],
                    linewidth=2,
                    color=_NON_SELECTED_COLOR,
                    pickradius=5,
                )
                window.im_axes.add_line(line)
                self._lines.append(line)
        artists.extend(self._lines)
        for i, lightcurve in enumerate(reducer.lightcurves):
            desired_color = _NON_SELECTED_COLOR
            if i == self._selected_line:
                desired_color = _SELECTED_COLOR
            if desired_color != self._lines[i].get_color():
                self._lines[i].set_color(desired_color)
        if self._selected_line == -1:
            return artists

        legend_handles = []
        for ind, variant_key in enumerate(state.variant_keys):
            if not self._show_all_lines and state.variant_key != variant_key:
                continue
            was_drawn = self._get_lightcurve_artist(
                ind, 
                variant_key,
                variant_key == state.variant_key,
                self.find_reducer(state, LightCurvesReducer, variant_key=variant_key).lightcurves[self._selected_line],
                window)
            if was_drawn:
                artists.append(self._lightcurves[variant_key])
                legend_handles.append(self._lightcurves[variant_key])
        self._legend = window.line_axes.legend(handles=list(legend_handles), loc="upper right")
        artists.append(self._legend)
        return artists

    def on_event(self, state: VizState, event: VizEvent) -> bool:
        if event.panel != Panel.IMAGE:
            return False
        if event.mouse_event is None:
            return False
        if event.name != "button_press_event":
            return False
        for i, line in enumerate(self._lines):
            contains_event, _ = line.contains(event.mouse_event)
            if contains_event:
                self._selected_line = i
                break
        self.request_draw()
        return True

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        axes.set_axis_on()
        button = Button(axes, "Show All")
        button.on_clicked(lambda *args: self._toggle_show_all())
        return [
            button,
        ]

    def _toggle_show_all(self) -> None:
        self._show_all_lines = not self._show_all_lines
        self.request_draw()

    def _get_lightcurve_artist(self,
                               ind: int,
                               variant_key: VariantKey,
                               primary: bool,
                               lightcurve: Lightcurve,
                               window: VizWindow,
    ) -> bool:
        x = np.linspace(
            0,
            (lightcurve.end_pos - lightcurve.start_pos).magnitude.value,
            len(lightcurve.magnitudes),
            endpoint=True,
        )
        if variant_key not in self._lightcurves:
            self._lightcurves[variant_key] = window.line_axes.plot(
                x,
                lightcurve.magnitudes,
                label=str(variant_key),
                alpha=1.0 if primary else 0.25)[0]
            window.line_axes.set_xlabel(lightcurve.end_pos.unit)
            window.line_axes.set_ylabel("Magnitudes")
        else:
            self._lightcurves[variant_key].set_data(
                x, lightcurve.magnitudes)
            self._lightcurves[variant_key].set_alpha(1.0 if primary else 0.25)
        if len(x) == 0:
            return False
        self.request_bounds(MirageAxes.LINE, 0, x[-1], np.min(lightcurve.magnitudes), np.max(lightcurve.magnitudes))
        return True

