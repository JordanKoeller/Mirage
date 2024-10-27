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
that is bound to and that the user controls. THe line graph at the top just
presents a secondary view on what is shown in the 2d canvas.

We can explore decoupling them in the future if there is a usecase, but it is
not necessary now.
"""

import logging
from typing import Type
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.widgets import Button

from mirage.lens_analysis.result import ExperimentResult
from mirage.viz import Viz

logger = logging.getLogger(__name__)

class VizWindow:
    def __init__(self):
        # General high-level organization
        self._fig: Figure = plt.figure(layout="tight", clear=True)
        self._gridspec = GridSpec(3, 1, self._fig, height_ratios=[4, 20, 1])
        self._top_axes = self._fig.add_subplot(self._gridspec[0, 0])
        self._bottom_axes = self._fig.add_subplot(self._gridspec[1, 0])

        # UI Elements
        self._ui_callbacks: dict[str, int] = {}
        self._ui_grid = self._gridspec[2, 0].subgridspec(1, 2)
        self._p_button_axes = self._fig.add_subplot(self._ui_grid[0, 0])
        self._n_button_axes = self._fig.add_subplot(self._ui_grid[0, -1])
        self._p_button = Button(self._p_button_axes, "Previous")
        self._n_button = Button(self._n_button_axes, "Next")
        self._ui_callbacks["p_button"] = self._p_button.on_clicked(
                self._prev_handler)
        self._ui_callbacks["n_button"] = self._n_button.on_clicked(
                self._next_handler)

        # The type of visualization being bound
        self._visualizer: Viz | None = None

        # More bookkeeping
        self._handlers: dict[str, list[callable]] = {}
        self._handler_funcs: dict[int, callable] = {}

    def bind_visualizer(self, visualizer: Viz) -> None:
        self._visualizer = visualizer
        self._visualizer.bind_window(self.refresh)

    def show(self):
        self._fig.show()
        self.refresh()

    def refresh(self):
        if self._visualizer:
            self._visualizer.draw(self._bottom_axes, self._top_axes)
        else:
            logger.warn("No visualizer bound to the window. Skipping draw.")

    def _next_handler(self, event):
        if self._visualizer:
            if not self._visualizer.to_next_simulation():
                logger.warn("No successor simulation. Cannot increment")
        self.refresh()

    def _prev_handler(self, event):
        if self._visualizer:
            if not self._visualizer.to_prev_simulation():
                logger.warn("No previous simulation. Cannot decrement")
        self.refresh()

    def _get_visualizer(self) -> Viz:
        """
        Inspects the bound Experiment, decides on the appropriate visualizer
        based on the reducer(s) in the Experiment, and returns an unbound
        visualizer of that type.
        """
        sim = self._experiment.simulation(self._simulation_id)
        possible_visualizers = []
        for v in Viz.get_visualizers():
            for r in sim.get_reducers():
                if type(r) in v.compatible_reducers():
                    possible_visualizers.append(v)
        if len(possible_visualizers) == 1:
            return possible_visualizers[0]()
        if len(possible_visualizers) == 0:
            raise ValueError("Could not find a compatible visualizer")
        print("Select which visualizere to bind:")
        for i, v in enumerate(possible_visualizers):
            print(f"[{i}]: {v.__name__}")
        v_i = int(input("> "))
        if v_i >= len(v) or v_i < 0:
            raise ValueError(f"Invalid index: {v_i}")
        return possible_visualizers[v_i]()

    # def _bind_to_axes(self, viz_type: Type[Viz], axes: Axes) -> Viz:
    #     viz_obj = viz_type(axes)
    #     # This could probably be cleaned up with a better way to deal
    #     # with multiple handlers on the same axes. But this works
    #     for evt_code, handler in viz_obj.get_event_handlers().items():
    #         if evt_code in self._handlers:
    #             self._handlers[evt_code].append((handler, axes))
    #         else:
    #             self._handlers[evt_code] = [(handler, axes)]
    #
    #             def handler_func(event):
    #                 for h, a in self._handlers[evt_code]:
    #                     if event.inaxes == a:
    #                         h(event)
    #
    #             cid = self._fig.canvas.mpl_connect(evt_code, handler_func)
    #             self._handler_funcs[cid] = handler_func
    #     return viz_obj
