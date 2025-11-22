from typing import List, Iterable
import logging

from matplotlib import animation
from matplotlib.artist import Artist

from mirage.viz.viz_state import VizState, Panel, VizEvent
from mirage.viz.window import VizWindow
from mirage.viz.controller import Controller
from mirage.util import Vec2D


logger = logging.getLogger(__name__)

ANIMATION_FRAMES_PER_SECOND = 20


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
        self._controllers: dict[str, Controller] = {}
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
            if self._controllers.get(layer_name).on_event(
                self._model, viz_event
            ):
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
        self._controllers[layer_name] = controller
        self._model.layers.append((layer_name, True))
        controller.reset()

    def draw(self, *args, **kwargs) -> Iterable[Artist]:
        if self._title is None:
            self._title = self._window.figure.suptitle(
                str(self._model.variant_key)
            )
        artists = []
        for layer_name, enabled in self._model.layers:
            if not enabled:
                continue
            controller = self._controllers.get(layer_name)
            for artist in controller.draw(self._model, self._window):
                artists.append(artist)
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
        self.draw()
        return True

    def prev_simulation(self) -> bool:
        if self._model.variant_key_index <= 0:
            return False
        self._model.variant_key_index -= 1
        self.draw()
        return True

    def show(self) -> None:
        self.draw()
        self._window.figure.show()
