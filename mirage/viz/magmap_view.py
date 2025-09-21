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

    def __init__(self):
        self._reducer: Optional[MagnificationMapReducer] = None
        self._line: Optional[Line2D] = None
        self._colormap = None

    def draw(self, canvas: Axes, line_graph: Axes) -> None:
        # Draw to main canvas
        canvas.set_axis_off()
        canvas.set_frame_on(True)
        if not self.magmap.has_output:
            raise ValueError("`magmap` did not have any output")
        magnitudes = self.magmap.magnitudes
        colormap = plt.get_cmap("RdBu")
        img = canvas.imshow(magnitudes, cmap=colormap)
        if self._colormap:
            self._colormap.remove()
        self._colormap = canvas.figure.colorbar(
            img, ax=canvas, pad=0.01, fraction=0.05)
        self._colormap.set_label("Magnitudes")
        canvas.figure.canvas.draw()

        # Overlay line, if present
        if self._line:
            canvas.add_line(self._line)


    def get_event_handlers(self):
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
    def magmap(self) -> MagnificationMapReducer | None:
        return self.simulation.get_reducer("magmap")

    @classmethod
    def compatible_reducers(cls):
        return [MagnificationMapReducer]
