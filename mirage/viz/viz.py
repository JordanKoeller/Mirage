from typing import List, Iterable
import logging
from dataclasses import dataclass

from matplotlib import animation
from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget

from mirage.viz.viz_state import VizState, Panel, VizEvent
from mirage.viz.window import VizWindow
from mirage.viz.controller import Controller
from mirage.util import Vec2D


logger = logging.getLogger(__name__)

ANIMATION_FRAMES_PER_SECOND = 10


@dataclass
class _ControllerState:
    controller: Controller
    enabled: bool
    stale: bool
    artists: List[Artist]
    widgets: List[AxesWidget]

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
        self._title = None

        for controller in controllers or []:
            self.bind_controller(controller)

        self._window.next_simulation_button.on_clicked(
            lambda *args: self.next_simulation()
        )
        self._window.previous_simulation_button.on_clicked(
            lambda *args: self.prev_simulation()
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

        self._animation = animation.FuncAnimation(
            self._window.figure,
            self.draw,
            interval=1000 / ANIMATION_FRAMES_PER_SECOND,
            blit=True,
            cache_frame_data=False,
        )

    def _on_mouse_event(self, event) -> None:
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
        for layer_name, enabled in self._model.layers[::-1]:
            if not enabled:
                continue
            controller_state = self._controllers.get(layer_name)
            consumed, stale = controller_state.controller.on_event(
                self._model, viz_event
            )
            controller_state.stale = stale
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
        layer_name = layer_name or type(controller).__name__
        self._controllers[layer_name] = _ControllerState(
            controller=controller,
            enabled=True,
            stale=True,
            artists=[],
            widgets=controller.bind_widgets(
                self._window.ui_axes(len(self._model.layers)),
                self._model,
            ),
        )
        self._model.layers.append((layer_name, True))
        controller.reset()

    def draw(self, *args, **kwargs) -> Iterable[Artist]:
        if self._title:
            self._title.set(text=str(self._model.variant_key))
        else:
            self._title = self._window.title().text(0,0, str(self._model.variant_key))
        artists = []
        for layer_name, enabled in self._model.layers:
            if not enabled:
                continue
            controller = self._controllers.get(layer_name)
            if controller.stale:
                controller.artists = controller.controller.draw(self._model, self._window)
                controller.stale = False
            artists.extend(controller.artists)
        self._window.figure.canvas.draw()
        return artists

    def enable_layer(self, layer_name: str, state: bool) -> bool:
        """
        Toggle a layer enabled or disabled.

        Returns True if a layer state swapped.
        """

    def next_simulation(self) -> bool:
        if self._model.variant_key_index >= len(self._model._variant_keys) - 1:
            return False
        self._model.variant_key_index += 1
        for k in self._controllers:
            self._controllers[k].stale = True
        return True

    def prev_simulation(self) -> bool:
        if self._model.variant_key_index <= 0:
            return False
        self._model.variant_key_index -= 1
        for k in self._controllers:
            self._controllers[k].stale = True
        return True

    def show(self) -> None:
        self.draw()
        self._window.figure.show()
