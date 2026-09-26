from typing import List
import logging
from dataclasses import dataclass
import uuid
from functools import partial
import contextlib

from matplotlib.widgets import CheckButtons
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.animation import FuncAnimation

from mirage.viz.viz_state import VizState, Panel, VizEvent
from mirage.viz.window import VizWindow, MirageAxes
from mirage.viz.controller import Controller, AxesBounds
from mirage.viz.ui_builder import PanelBuilder, ButtonBuilder
from mirage.util import Vec2D, Dictify, Stopwatch, RepeatLogger
from mirage.settings import load_settings
from mirage.viz import VizConfig


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
  panel: QtWidgets.QGroupBox


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
    self._needs_clear = False

    self.bind_variants()

    for controller in controllers or []:
      self.bind_controller(controller)

    self._window.sim_next_button.clicked.connect(self.next_simulation)
    self._window.sim_prev_button.clicked.connect(self.prev_simulation)
    self._window.sim_animate_button.clicked.connect(self.animate_simulation)

    self._window.figure.canvas.mpl_connect(
      "button_press_event", lambda event: self._on_mouse_event(event)
    )
    self._window.figure.canvas.mpl_connect(
      "button_release_event", lambda event: self._on_mouse_event(event)
    )
    self._window.figure.canvas.mpl_connect(
      "motion_notify_event", lambda event: self._on_mouse_event(event)
    )
    self._window.export_button.clicked.connect(self._export)

    self._timer = self._window.new_timer()
    self._window.timer.add_callback(self.draw)
    self._window.timer.start()
    self.show()

  @contextlib.contextmanager
  def pause_timer(self):
    self._timer.stop()
    yield
    self._timer = self._window.new_timer()
    self._timer.add_callback(self.draw)
    self._timer.start()

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

  def bind_variants(self):
    self._window.add_panel(
      "variant_controls",
      PanelBuilder("Active Variants")
      .add_row(
        *[
          (
            ButtonBuilder("checkbox")
            .set_label(k)
            .set_active(True)
            .set_callback(partial(self._toggle_locked_variant, k))
            .build()
          )
          for k in self._model.variant_key
        ]
      )
      .build(),
    )

  def _toggle_locked_variant(self, variant_name: str, on: bool) -> None:
    if on:
      self._model.locked_variants.remove(variant_name)
      return
    self._model.locked_variants.add(variant_name)

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
      panel=controller.bind_widgets(self._model)
      .set_title(layer_name)
      .set_checkbox_callback(partial(self.toggle_layer, layer_name))
      .build(),
    )
    self._controllers[layer_name] = controller_state
    self._window.add_panel(layer_name, controller_state.panel)
    self._model.layers.append(layer_name)
    controller.reset()

  def draw(self, *args, force: bool = False, **kwargs) -> None:
    with self._stopwatch.timeit():
      if self._needs_clear:
        self._window.clear_plots()
        self._needs_clear = True
      new_realtime_result = self._model.realtime and self._model.ingest_results()
      bounds = None
      for layer_name in self._model.layers:
        controller = self._controllers.get(layer_name)
        if not controller.enabled:
          continue
        did_draw = controller.controller.do_draw(
          self._model,
          self._window,
          force=force or new_realtime_result or self._animate,
        )
        if not did_draw:
          continue
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
    return

  def toggle_layer(self, layer_name: str, on) -> None:
    """
    Toggle a layer enabled or disabled.
    """
    for k in self._controllers:
      if k == layer_name:
        self._controllers[layer_name].enabled = on
      self._controllers[layer_name].controller.reset()
      self._controllers[layer_name].controller.request_draw()

  def next_simulation(self, rollover: bool = False) -> bool:
    if not self._model.next_variant(rollover):
      return False
    for k in self._controllers:
      self._controllers[k].controller.request_draw()
    self._window.set_title(str(self._model.variant_key))
    self._window.set_text(Dictify.to_yaml(self._model.simulation_result().simulation))
    return True

  def prev_simulation(self) -> bool:
    if not self._model.prev_variant():
      return False
    for k in self._controllers:
      self._controllers[k].controller.request_draw()
    self._window.set_title(str(self._model.variant_key))
    self._window.set_text(Dictify.to_yaml(self._model.simulation_result().simulation))
    return True

  def animate_simulation(self) -> bool:
    self._animate = not self._animate

  def show(self) -> None:
    self._window.set_title(str(self._model.variant_key))
    self._window.set_text(Dictify.to_yaml(self._model.simulation_result().simulation))
    self.draw(force=True)
    self._window.show()

  def _export(self) -> None:
    """
    Exports the current figure to file.

    If Viz is animating, a mp4 video of the animation is exported. Otherwise a still
    png is exported.
    """
    if not self._animate:
      fname = self._window.pick_file("image")
      if not fname:
        print("Image not exported")
        return
      self._window.figure.savefig(fname, format="png")
      return
    self._window.timer.stop()
    fname = self._window.pick_file("video")
    if not fname:
      print("Video not exported")
      return
    num_frames = 0
    for i, (variant, active) in enumerate(self._model.variant_keys):
      if active:
        num_frames += 1
        self._model._variant_key_index = min(self._model._variant_key_index, i)
    progress_dialog = self._window.progress_dialog(num_frames * 10)
    progress_dialog.show()
    QtWidgets.QApplication.processEvents()

    def progress(i, n):
      progress_dialog.setValue(i)
      QtWidgets.QApplication.processEvents()

    settings = load_settings(VizConfig)
    with self.pause_timer():
      animation = FuncAnimation(
        self._window.figure,
        frames=num_frames * 10,
        func=partial(self.draw, force=True),
        interval=1
      )
      animation.save(
        fname,
        progress_callback=progress,
        fps=settings.max_fps
      )
      progress(num_frames * 10, num_frames * 10)
      progress_dialog.setCancelButtonText("Done")
      animation.pause()

  def _create_variants_checkboxes(self) -> None:
    variant_labels = {}
    for variant in self._model._experiment.experiment._variants.values():
      try:
        uuid.UUID(variant.tag)
        variant_labels[variant.name] = variant
      except ValueError:
        variant_labels[variant.tag] = variant
    self._variant_checkbuttons = CheckButtons(
      self._window.variants_checkbox,
      labels=list(variant_labels.keys()),
      actives=[True for _ in range(len(variant_labels))],
    )

    def on_click(label: str, *args, **kwargs) -> None:
      for i, variant in enumerate(self._model.locked_variants):
        if variant.name == label or variant.tag == label:
          self._model.locked_variants.pop(i)
          return
      self._model.locked_variants.append(label)

    self._variant_checkbuttons.on_clicked(on_click)

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
          self._window.line_axes.set_ylim(cy + dy, cy - dy)
      self._bounds[axis] = bounds[axis]
