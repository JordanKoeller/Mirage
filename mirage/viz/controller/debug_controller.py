import numpy as np
from typing import Iterable

from mirage.viz.window import VizWindow, MirageAxes
from mirage.calc import Reducer
from mirage.viz.viz_state import VizState
from mirage.viz.controller import Controller

from matplotlib.widgets import AxesWidget, CheckButtons
from matplotlib.artist import Artist
from matplotlib.axes import Axes

_RENDER_SOURCE_PLANE = "Render Source Plane"
_RENDER_LENS_PLANE = "Render Lens Plane"
_RENDER_STARS = "Render Stars"


class DebugController(Controller):
  def __init__(self, reducer_name: str | None = None) -> None:
    Controller.__init__(self)
    self._reducer_name = reducer_name
    self.reset()

  @property
  def supported_reducers(self) -> list[type[Reducer]]:
    # DebugController does not depend on reducers, so return empty list
    #   to signify it does not have a dependency on a Reducer.
    return []

  def reset(self) -> None:
    self._render_controls = {
      _RENDER_SOURCE_PLANE: False,
      _RENDER_LENS_PLANE: False,
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
      if not self._render_controls[k]:
        continue  # Don't draw things that don't need rendered.
      if k == _RENDER_SOURCE_PLANE:
        tl, br = state.source_region.to(state.length_unit).span
        self.request_bounds(
          MirageAxes.IMAGE, tl.x.value, br.x.value, tl.y.value, br.y.value
        )
        bounds = state.source_region.outline.to(state.length_unit)
        if self._artists[k]:
          self._artists[k].set_data(bounds[:, 0], bounds[:, 1])
        else:
          self._artists[k] = window.im_axes.plot(
            bounds[:, 0], bounds[:, 1], label="Source Region"
          )[0]
      if k == _RENDER_LENS_PLANE:
        tl, br = state.lens_region.to(state.length_unit).span
        self.request_bounds(
          MirageAxes.IMAGE, tl.x.value, br.x.value, tl.y.value, br.y.value
        )
        bounds = state.lens_region.outline.to(state.length_unit)
        if self._artists[k]:
          self._artists[k].set_data(bounds[:, 0], bounds[:, 1])
        else:
          self._artists[k] = window.im_axes.plot(
            bounds[:, 0], bounds[:, 1], label="Lense Region"
          )[0]
      if k == _RENDER_STARS:
        ray_tracer = state.simulation_result().simulation.get_ray_tracer()
        stars_mass, stars_positions = ray_tracer.starfield.get_starfield(
          ray_tracer.star_mass, ray_tracer.starfield_angular_radius
        )
        stars_positions = stars_positions.to(state.length_unit)
        self.request_bounds(
          MirageAxes.IMAGE,
          np.min(stars_positions[:, 0].value),
          np.max(stars_positions[:, 0].value),
          np.min(stars_positions[:, 1].value),
          np.max(stars_positions[:, 1].value),
        )
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
            s=stars_mass.to("solMass").value,
            label="Stars",
          )
    ret = [self._artists[k] for k in self._artists if self._artists[k]]
    return ret

  def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
    axes.set_axis_on()
    buttons = CheckButtons(
      axes,
      labels=[_RENDER_SOURCE_PLANE, _RENDER_LENS_PLANE, _RENDER_STARS],
      actives=[
        self._render_controls[_RENDER_SOURCE_PLANE],
        self._render_controls[_RENDER_LENS_PLANE],
        self._render_controls[_RENDER_STARS],
      ],
    )
    buttons.on_clicked(self._on_button_pressed)
    return [buttons]

  def _on_button_pressed(self, label, *args, **kwargs) -> None:
    self._render_controls[label] = not self._render_controls[label]
    self.request_draw()
