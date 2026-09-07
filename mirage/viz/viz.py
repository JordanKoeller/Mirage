from typing import List, Iterable
import logging
from dataclasses import dataclass

from matplotlib import animation
from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget, Button, CheckButtons

from mirage.settings import load_settings
from mirage.viz.viz_state import VizState, Panel, VizEvent
from mirage.viz.window import VizWindow, MirageAxes
from mirage.viz.controller import Controller, AxesBounds
from mirage.util import Vec2D, Dictify, Stopwatch, RepeatLogger
from mirage.viz.viz_settings import VizConfig


logger = logging.getLogger(__name__)

fps_logger = RepeatLogger(50, logger)


def _merge_bounds(
  merge_into: dict[MirageAxes, AxesBounds],
  merge_from: dict[MirageAxes, AxesBounds],
) -> None:
  """
  Merge two AxesBounds dictionaries, updating merge_into inplace.
  """
  for axis in MirageAxes:
    if merge_from[axis] is None:
      continue
    if merge_into[axis] is None:
      merge_into[axis] = merge_from[axis]
      continue
    merge_into[axis].merge(merge_from[axis])


@dataclass
class _ControllerState:
  controller: Controller
  enabled: bool
  control_button: Button
  artists: List[Artist]
  widgets: List[AxesWidget]

  def disable(self) -> None:
    if not self.enabled:
      return
    self.enabled = False
    for artist in self.artists:
      artist.remove()
    self.controller.reset()


class Viz:
  """
  Container class for `viz`'s MVC system, as well as an api for interracting
  with the respective parts.
  """

  def __init__(
    self,
    model: VizState,
    view: VizWindow,
    controllers: List[Controller] | None = None,
  ) -> None:
    self._model = model
    self._window = view
    self._controllers: dict[str, _ControllerState] = {}
    self._animate = False
    self._bounds = {axis: None for axis in MirageAxes}
    self._stopwatch = Stopwatch()

    for controller in controllers or []:
      self.bind_controller(controller)

    self._window.next_simulation_button.on_clicked(lambda *args: self.next_simulation())
    self._window.previous_simulation_button.on_clicked(
      lambda *args: self.prev_simulation()
    )
    self._window.animate_simulation_button.on_clicked(
      lambda *args: self.animate_simulation()
    )
    self._window.figure.canvas.mpl_connect(
      "button_press_event", lambda event: self._on_mouse_event(event)
    )
    self._window.figure.canvas.mpl_connect(
      "button_release_event", lambda event: self._on_mouse_event(event)
    )
    self._window.figure.canvas.mpl_connect(
      "motion_notify_event", lambda event: self._on_mouse_event(event)
    )

    self.show()

    config = load_settings(VizConfig)

    self._animation = animation.FuncAnimation(
      self._window.figure,
      self.draw,
      interval=1000 / config.max_fps,
      blit=False,
      cache_frame_data=False,
    )

  def _on_mouse_event(self, event) -> None:
    tool = self._window.figure.canvas.toolbar.mode
    if tool:
      # Matplotlib special tool is selected, so ignore events.
      return
    panel = None
    if event.inaxes == self._window.im_axes:
      panel = Panel.IMAGE
    if event.inaxes == self._window.line_axes:
      panel = Panel.LINE
    if panel is None:
      logger.debug("Had MouseEvent with unmatched Axes.")
      return
    viz_event = VizEvent(
      panel=panel,
      screen_pos=Vec2D.unitless(event.xdata, event.ydata),
      name=event.name,
      mouse_event=event,
    )
    for layer_name in self._model.layers[::-1]:
      controller_state = self._controllers.get(layer_name)
      if not controller_state.enabled:
        continue
      consumed = controller_state.controller.on_event(self._model, viz_event)
      if consumed:
        break

  def _on_key_event(self, event) -> None:
    pass

  def bind_controller(
    self, controller: Controller, layer_name: str | None = None
  ) -> None:
    """
    Add a new controller to Viz. The new controller is added as the top layer.
    """
    supported = len(controller.supported_reducers) == 0
    for reducer in controller.supported_reducers:
      for available_reducer in self._model.simulation_result():
        if isinstance(available_reducer, reducer):
          supported = True
          break
    if not supported:
      logger.info(
        f"No compatible reducer found for controller {controller}. Binding as Disabled."
      )
    logger.info(f"Activating Controller {controller}.")
    layer_name = layer_name or type(controller).__name__
    controller.request_draw()
    controller_state = _ControllerState(
      controller=controller,
      enabled=supported,
      control_button=CheckButtons(
        self._window.layer_control_axes(len(self._model.layers)),
        labels=[f"Enable {layer_name}"],
        actives=[supported],
      ),
      artists=[],
      widgets=controller.bind_widgets(
        self._window.ui_axes(len(self._model.layers)),
        self._model,
      ),
    )
    controller_state.control_button.on_clicked(
      lambda *args: self.toggle_layer(layer_name)
    )
    self._controllers[layer_name] = controller_state
    self._model.layers.append(layer_name)
    controller.reset()

  def draw(self, *args, force: bool = False, **kwargs) -> Iterable[Artist]:
    with self._stopwatch.timeit():
      new_realtime_result = self._model.realtime and self._model.ingest_results()
      artists = []
      artists.extend(self._window.title_artists())
      bounds = None
      for layer_name in self._model.layers:
        controller = self._controllers.get(layer_name)
        artists.append(controller.control_button)
        if not controller.enabled:
          if controller.artists:
            for artist in controller.artists:
              try:
                artist.remove()
              except:
                pass
            controller.controller.reset()
            controller.artists = []
            did_draw = True
          continue
        did_draw, artists = controller.controller.do_draw(
          self._model,
          self._window,
          force=force or new_realtime_result or self._animate,
        )
        if did_draw:
          controller.artists = artists
        controller = self._controllers.get(layer_name)
        artists.extend(controller.artists)
        if bounds is None:
          bounds = controller.controller._bounds
        else:
          _merge_bounds(bounds, controller.controller._bounds)
      self._update_axes_bounds(bounds)
      self._window.draw()
      if self._animate:
        self.next_simulation(rollover=True)
    if fps_logger.info(f"{1 / self._stopwatch.avg_elapsed_seconds()} fps"):
      self._stopwatch.reset()
    return artists

  def toggle_layer(self, layer_name: str) -> None:
    """
    Toggle a layer enabled or disabled.
    """
    if self._controllers[layer_name].enabled:
      self._controllers[layer_name].enabled = False
      for widget in self._controllers[layer_name].widgets:
        widget.set_active(False)
    else:
      self._controllers[layer_name].enabled = True
      for widget in self._controllers[layer_name].widgets:
        widget.set_active(True)

  def next_simulation(self, rollover: bool = False) -> bool:
    if not self._model.next_variant(rollover):
      return False
    for k in self._controllers:
      self._controllers[k].controller.request_draw()
    self._window.set_title(str(self._model.variant_key))
    self._window.text_box.set(
      text=Dictify.to_yaml(self._model.simulation_result().simulation)
    )
    return True

  def prev_simulation(self) -> bool:
    if not self._model.prev_variant():
      return False
    for k in self._controllers:
      self._controllers[k].controller.request_draw()
    self._window.set_title(str(self._model.variant_key))
    self._window.text_box.set(
      text=Dictify.to_yaml(self._model.simulation_result().simulation)
    )
    return True

  def animate_simulation(self) -> bool:
    self._animate = not self._animate
    if self._animate:
      # self._window.animate_simulation_button.set_text("Stop Animation")
      self._window.next_simulation_button.set_active(False)
      self._window.previous_simulation_button.set_active(False)
    else:
      # self._window.animate_simulation_button.set_text("Animation")
      self._window.next_simulation_button.set_active(True)
      self._window.previous_simulation_button.set_active(True)

  def show(self) -> None:
    self._window.set_title(str(self._model.variant_key))
    self._window.text_box.set(
      text=Dictify.to_yaml(self._model.simulation_result().simulation)
    )
    self.draw(force=True)
    self._window.show()

  def _update_axes_bounds(self, bounds: dict[MirageAxes, AxesBounds] | None) -> None:
    if bounds is None:
      return
    for axis in MirageAxes:
      if bounds[axis] is None:
        continue
      if self._bounds[axis] == bounds[axis]:
        continue
      cx = (bounds[axis].x_min + bounds[axis].x_max) / 2
      dx = abs(cx - bounds[axis].x_min) * 1.05
      cy = (bounds[axis].y_min + bounds[axis].y_max) / 2
      dy = abs(cy - bounds[axis].y_min) * 1.05
      match axis:
        case MirageAxes.IMAGE:
          self._window.im_axes.set_xlim(cx - dx, cx + dx)
          self._window.im_axes.set_ylim(cy + dy, cy - dy)
        case MirageAxes.LINE:
          self._window.line_axes.set_xlim(cx - dx, cx + dx)
          self._window.line_axes.set_ylim(cy - dy, cy + dy)
      self._bounds[axis] = bounds[axis]
