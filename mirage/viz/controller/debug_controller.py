import sys
from mirage.viz.window import VizWindow
from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz.viz_state import VizState, VizEvent, Panel
from mirage.viz.controller import Controller
from mirage.util import Index2D, VariantKey, Vec2D

from matplotlib.lines import Line2D
from matplotlib.widgets import AxesWidget, Button, CheckButtons
from matplotlib.artist import Artist

_RENDER_SOURCE_PLANE = "Render Source Plane"
_RENDER_LENS_PLANE = "Render Lens Plane"
_RENDER_STARS = "Render Stars"

class DebugController(Controller):
    def __init__(self, reducer_name: str | None = None) -> None:
        Controller.__init__(self)
        self._reducer_name = reducer_name
        self.reset()

    def reset(self) -> None:
        self._render_controls = {
            _RENDER_SOURCE_PLANE: True,
            _RENDER_LENS_PLANE: True,
            _RENDER_STARS: False,
        }
        self._artists = {
            _RENDER_SOURCE_PLANE: None,
            _RENDER_LENS_PLANE: None,
            _RENDER_STARS: None,
        }

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        for k in self._render_controls:
            if self._artists[k]:
                self._artists[k].set(visible=self._render_controls[k])
            if k == _RENDER_SOURCE_PLANE:
                bounds = state.source_region.outline.to("uas")
                if self._artists[k]:
                    self._artists[k].set_data(bounds[:, 0], bounds[:, 1])
                else:
                    self._artists[k] = window.im_axes.plot(
                        bounds[:, 0], bounds[:, 1], label="Source Region")[0]
            if k == _RENDER_LENS_PLANE:
                bounds = state.lens_region.outline.to("uas")
                if self._artists[k]:
                    self._artists[k].set_data(bounds[:, 0], bounds[:, 1])
                else:
                    self._artists[k] = window.im_axes.plot(
                        bounds[:, 0], bounds[:, 1], label="Lense Region")[0]
            if k == _RENDER_STARS:
                ray_tracer = state.simulation_result.simulation.get_ray_tracer()
                stars_mass, stars_positions = ray_tracer.starfield.get_starfield(
                    ray_tracer.star_mass, ray_tracer.starfield_angular_radius
                )
                stars_positions = stars_positions.to("uas")
                if self._artists[k]:
                    self._artists[k].set_offsets(
                        stars_positions,
                    )
                    self._artists[k].set(
                        sizes=stars_mass.to("solMass").value,
                    )
                else:
                    self._artists[k] = window.im_axes.scatter(
                        stars_positions[:, 0],
                        stars_positions[:, 1],
                        s=stars_mass.to("solMass").value, label="Stars")
        ret = [self._artists[k] for k in self._artists if self._artists[k]]
        return ret


    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        axes.set_axis_on()
        buttons = CheckButtons(
            axes,
            labels=[
                _RENDER_SOURCE_PLANE,
                _RENDER_LENS_PLANE,
                _RENDER_STARS
            ],
            actives=[
                self._render_controls[_RENDER_SOURCE_PLANE],
                self._render_controls[_RENDER_LENS_PLANE],
                self._render_controls[_RENDER_STARS],
            ]
        )
        buttons.on_clicked(self._on_button_pressed)
        return [buttons]

    def _on_button_pressed(self, label, *args, **kwargs) -> None:
        print("Updating controller state", label)
        self._render_controls[label] = not self._render_controls[label]
        self.request_draw()


