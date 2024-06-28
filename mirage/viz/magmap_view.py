from typing import Optional

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz import Viz


@Viz.register
class MagmapView(Viz):
    """
    Presents a unified view for visualizing and manipulating Magnification
    Maps. Supports overlaying lightcurves onto a Magmap as well.

    The characteristics are as follows:

        + The view consists of a magnification map on the bottom with an
          included colorbar, and a plot above to display the lightcurve.
        + When a magnification map is shown, it fills the magnification map
          in the bottom area. The coloring should auto-calibrate to have white
          as zero-mag, then red / blue diverge to high-magnitude and
          low-magnitude, respectively.
        + Click/dragging through the magmap will allow for creation of a
          lightcurve by sampling the pixel data.


    """

    def __init__(self, image_axes: Axes):
        self._setup_axes(image_axes)
        self._reducer: Optional[MagnificationMapReducer] = None
        self._line: Optional[Line2D] = None

    @classmethod
    def for_window(cls, window):
        return window.bind_bottom_view(cls)

    @staticmethod
    def new() -> "MagmapView":
        figure = plt.figure(
            layout="tight",
            clear=True,
        )
        axes = figure.add_subplot()
        return MagmapView(axes)

    def show(self, reducer: MagnificationMapReducer):  # type: ignore
        if not reducer.has_output:
            raise ValueError("`reducer` did not have any output")
        self._reducer = reducer
        magnitudes = reducer.magnitudes
        img = self.image_axes.imshow(magnitudes, cmap=self.colormap)
        cb = self._figure.colorbar(
            img, ax=self.image_axes, pad=0.01, fraction=0.05
        )
        cb.set_label("Magnitudes")
        self._figure.show()

    def _setup_axes(self, image_axes: Axes):
        self.colormap = plt.get_cmap("RdBu")
        self.image_axes = image_axes
        self.image_axes.set_axis_off()
        self.image_axes.set_frame_on(True)

    def get_event_handlers(self):
        return {}
        return {
            "button_press_events": self._on_press,
            "button_release_events": self._on_release,
            "motion_notify_events": self._on_move,
        }

    def _on_press(self, event):
        self._line = Line2D(
            [event.xdata, 0], [event.ydata, 0], color="r", antialiased=True
        )

    def _on_move(self, event):
        if self._line is None:
            return
        self._line.set_xdata()
        # TODO: Finish this.

    def _on_release(self, event):
        pass

    @property
    def _figure(self):
        return self.image_axes.get_figure()

    @classmethod
    def compatible_reducers(cls):
        return [MagnificationMapReducer]
