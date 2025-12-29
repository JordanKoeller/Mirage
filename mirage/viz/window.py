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
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.widgets import Button

logger = logging.getLogger(__name__)

MAX_LAYERS = 4


class VizWindow:
    def __init__(self):
        # General high-level organization
        self._fig: Figure = plt.figure(layout="tight", clear=True)
        self._gridspec = GridSpec(2, 1, self._fig, height_ratios=[4, 20])
        self._top_axes = self._fig.add_subplot(self._gridspec[0, 0])
        self._bottom_gridspec = self._gridspec[1, 0].subgridspec(1, 2, width_ratios=[1, 5])
        self._bottom_axes = self._fig.add_subplot(self._bottom_gridspec[0, 1])

        # UI Input Elements
        self._stock_ui = self._bottom_gridspec[0,0].subgridspec(MAX_LAYERS + 2, 1) # title, next/prev, and then MAX_LAYERS layer UIs.
        self._widget_axes = [self._fig.add_subplot(self._stock_ui[i + 2, 0]) for i in range(0, MAX_LAYERS)]
        self._buttons_ui = self._stock_ui[1,0].subgridspec(1, 2)
        self._p_button_axes = self._fig.add_subplot(self._buttons_ui[0, 0])
        self._n_button_axes = self._fig.add_subplot(self._buttons_ui[0, -1])
        self._p_button = Button(self._p_button_axes, "Previous")
        self._n_button = Button(self._n_button_axes, "Next")

        self._desc_box = self._fig.add_subplot(self._stock_ui[0,0])
        self._desc_box.set_axis_off()
        self._desc_box.set_frame_on(True)

        self.im_axes.set_axis_off()
        self.im_axes.set_frame_on(True)
        self.im_axes.invert_yaxis()

    def title(self) -> Axes:
        return self._desc_box

    @property
    def figure(self) -> Figure:
        return self._fig

    @property
    def im_axes(self) -> Axes:
        return self._bottom_axes

    @property
    def line_axes(self) -> Axes:
        return self._top_axes

    def ui_axes(self, index: int) -> Axes:
        if index < MAX_LAYERS:
            return self._widget_axes[index]
        raise ValueError(f"Invalid layer index: {index}")

    @property
    def next_simulation_button(self) -> Button:
        return self._n_button

    @property
    def previous_simulation_button(self) -> Button:
        return self._p_button

    def draw(self) -> None:
        self.figure.canvas.draw_idle()
