from typing import Type
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from mirage.viz import Viz


class VizWindow:
    def __init__(self):
        self._fig: Figure = plt.figure(layout="tight", clear=True)
        self._gridspec = GridSpec(2, 1, self._fig, height_ratios=[1, 5])
        self._top_axes = self._fig.add_subplot(self._gridspec[0, 0])
        self._bottom_axes = self._fig.add_subplot(self._gridspec[1, 0])
        self._handlers: dict[str, list[callable]] = {}
        self._handler_funcs: dict[int, callable] = {}

    def bind_top_view(self, viz: Type[Viz]) -> Viz:
        return self._bind_to_axes(viz, self._top_axes)

    def bind_bottom_view(self, viz: Type[Viz]) -> Viz:
        return self._bind_to_axes(viz, self._bottom_axes)

    def show(self):
        self._fig.show()

    def _bind_to_axes(self, viz_type: Type[Viz], axes: Axes) -> Viz:
        viz_obj = viz_type(axes)
        # This could probably be cleaned up with a better way to deal
        # with multiple handlers on the same axes. But this works
        for evt_code, handler in viz_obj.get_event_handlers().items():
            if evt_code in self._handlers:
                self._handlers[evt_code].append((handler, axes))
            else:
                self._handlers[evt_code] = [(handler, axes)]

                def handler_func(event):
                    for h, a in self._handlers[evt_code]:
                        if event.inaxes == a:
                            h(event)

                cid = self._fig.canvas.mpl_connect(evt_code, handler_func)
                self._handler_funcs[cid] = handler_func
        return viz_obj
