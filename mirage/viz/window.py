"""
Viz Window
==========

Presents a generic canvas on which to bind specific visualizations.

The canvas consists of:
    1. A linear plot across the top
    2. A 2D canvas on which to draw heatmaps, images, animations, etc.
    3. A spot for a colorbar next to the 2d plot for a scale.
    3. A few UI Widgets for simple controls:
        1. Next / Prev buttons for stepping through a sequence of simulations.
        2. A dropdown to select which sequence of simulations to step through???
        3. Buttons to show/hide the plot or 2d canvas.
        4. If showing an animation, framerate controls.

How is it all wired up?

For this initial implementation, I'm going to make the 2d canvas the primary thing
that is bound to and that the user controls. The line graph at the top just
presents a secondary view on what is shown in the 2d canvas.

We can explore decoupling them in the future if there is a usecase, but it is
not necessary now.
"""
import logging
import dataclasses
import enum

from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.widgets import Button
from matplotlib.text import Text

logger = logging.getLogger(__name__)

MAX_LAYERS = 4
WIDGET_ROWS = MAX_LAYERS + 1
PADDING=0.08

class MirageAxes(enum.Enum):
    IMAGE = "IMAGE"
    LINE = "LINE"

class VizWindow:
    def __init__(self):
        # General high-level organization
        self._plot_fig: Figure = plt.figure(clear=True, layout="constrained", figsize=[6.0, 6.0])
        self._plot_axes = self._plot_fig.subplot_mosaic(
            [
                ["title"],
                ["plot"],
                ["image"],
            ],
            height_ratios=[1, 5, 25],
            per_subplot_kw={
                "title": {"frame_on": False, "xticks": [], "yticks": []},
                "image": {"frame_on": True},
            },
        )

        # UI Input Elements
        self._widgets_fig = plt.figure(clear=True, layout="constrained", frameon=False, figsize=[6.4, 8.0])
        self._widget_axes = self._widgets_fig.subplot_mosaic(
            [
              ["title"] * 6,
              ["previous", "previous", "animate","animate","next","next"],
              *[[f"l{i}", f"l{i}", f"l{i}", f"l{i}", f"control_l{i}",f"control_l{i}",] for i in range(MAX_LAYERS)],
              ["text"] * 6
            ],
            subplot_kw={"frame_on": True, "xticks": [], "yticks": []},
            height_ratios=[1, 3, *([3] * MAX_LAYERS), 1],
            per_subplot_kw={
                "title": {"frame_on": False, "xticks": [], "yticks": []},
            },
        )
        self._p_button = Button(self._widget_axes["previous"], "Previous")
        self._n_button = Button(self._widget_axes["next"], "Next")
        self._a_button = Button(self._widget_axes["animate"], "Animate")
        self._text_box = self._widget_axes["text"].text(0, 1, "")


        self._plot_axes["image"].invert_yaxis()

        self._plot_fig_title = self._plot_axes["title"].text(0, 0, "")
        self._widgets_fig_title = self._widget_axes["title"].text(0, 0, "")

    def title_artists(self) -> list[Text]:
        return [self._plot_fig_title, self._widgets_fig_title]

    def set_title(self, text: str) -> None:
        self._plot_fig_title.set(text=text)
        self._widgets_fig_title.set(text=text)

    @property
    def figure(self) -> Figure:
        return self._plot_fig

    @property
    def im_axes(self) -> Axes:
        return self._plot_axes["image"]

    @property
    def line_axes(self) -> Axes:
        return self._plot_axes["plot"]

    def ui_axes(self, index: int) -> Axes:
        if index < MAX_LAYERS:
            return self._widget_axes[f"l{index}"]
        raise ValueError(f"Invalid layer index: {index}")

    def layer_control_axes(self, index: int) -> Axes:
        if index < MAX_LAYERS:
            return self._widget_axes[f"control_l{index}"]
        raise ValueError(f"Invalid layer index: {index}")

    @property
    def next_simulation_button(self) -> Button:
        return self._n_button

    @property
    def previous_simulation_button(self) -> Button:
        return self._p_button

    @property
    def animate_simulation_button(self) -> Button:
        return self._a_button

    @property
    def text_box(self) -> Axes:
        return self._text_box

    def show(self) -> None:
        self._widgets_fig.show()
        self._plot_fig.show()

    def draw(self) -> None:
        self._plot_fig.canvas.draw_idle()
        self._widgets_fig.canvas.draw_idle()
