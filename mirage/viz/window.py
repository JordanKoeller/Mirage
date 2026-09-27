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

import enum
import logging
import pathlib

from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.qt_compat import QtWidgets, QtCore
from matplotlib.figure import Figure

from mirage.viz import VizConfig
from mirage.viz.ui_builder import PanelBuilder, ButtonBuilder
from mirage.settings import load_settings

logger = logging.getLogger(__name__)


class MirageAxes(enum.Enum):
  IMAGE = "IMAGE"
  LINE = "LINE"


class FigWindow(QtWidgets.QMainWindow):
  def __init__(self):
    super().__init__()
    self._main = QtWidgets.QWidget()
    self.setCentralWidget(self._main)
    self._layout = QtWidgets.QVBoxLayout(self._main)
    self._figure = FigureCanvas(Figure(layout="constrained", figsize=(6.0, 6.0)))
    self._plot_axes = self._figure.figure.subplot_mosaic(
      [
        ["plot"],
        ["image"],
      ],
      height_ratios=[5, 25],
      per_subplot_kw={
        "image": {"frame_on": True},
      },
    )
    self._layout.addWidget(NavigationToolbar(self._figure, self))
    self._layout.addWidget(self._figure)

  @property
  def figure(self) -> Figure:
    return self._figure

  @property
  def im_axes(self) -> Axes:
    return self._plot_axes["image"]

  @property
  def line_axes(self) -> Axes:
    return self._plot_axes["plot"]


class WidgetsWindow(QtWidgets.QMainWindow):
  def __init__(self):
    super().__init__()
    self._panels = {}

    self._main = QtWidgets.QWidget()
    self.setCentralWidget(self._main)
    self._title = QtWidgets.QLabel("Viz", alignment=QtCore.Qt.AlignCenter)

    self._vbox = QtWidgets.QVBoxLayout(self._main)
    self._vbox.addWidget(self._title)

    self.sim_prev_button = ButtonBuilder("push").set_label("Previous").build()
    self.sim_next_button = ButtonBuilder("push").set_label("Next").build()
    self.sim_animate_button = (
      ButtonBuilder("checkbox").set_label("Animate").set_active(False).build()
    )

    self.export_button = ButtonBuilder("push").set_label("Export Figure").build()

    panel = (
      PanelBuilder("Simulation Controls")
      .add_row(
        self.sim_animate_button,
        self.sim_prev_button,
        self.sim_next_button,
      )
      .add_row(self.export_button)
      .build()
    )
    self._vbox.addWidget(panel)

    self._text_box = QtWidgets.QTextEdit()
    self._vbox.addWidget(self._text_box)


class VizWindow:
  def __init__(self):
    # I call plt.figure() to initialize the matplotlib context. In the future, I should
    # figure out a way to remove this call.
    plt.figure()
    self._figure_window = FigWindow()
    self._widgets_window = WidgetsWindow()
    self._locked_variants = set()
    settings = load_settings(VizConfig)
    self._timer = self._figure_window._figure.new_timer(1000 / settings.max_fps)

  def new_timer(self):
    settings = load_settings(VizConfig)
    return self._figure_window._figure.new_timer(1000 / settings.max_fps)

  def add_panel(self, key: str, panel: QtWidgets.QWidget) -> None:
    if key in self._widgets_window._panels:
      return
    i = len(self._widgets_window._panels)
    self._widgets_window._panels[key] = (panel, i)
    self._widgets_window._vbox.insertWidget(i + 2, panel)

  def set_title(self, title: str) -> None:
    self._widgets_window._title.setText(title)

  def set_text(self, text: str) -> None:
    self._widgets_window._text_box.setText(text)

  def pick_file(self, filetype: str, readonly: bool = False) -> str | None:
    """
    Opens a File picker dialog and returns the selected file.

    Args:
      filetype (str) - Filetype that should be selected. Supports 'image', 'video', 'dir'
        to request an image file, video file, or directory (respectively). If any other
        value is specified it is assumed to be a regex pattern to match.
      readonly (bool) - If true, returns an existing file, otherwise it may return a file
        that does not exist. Defaults to False
    """
    caption = "Open" if readonly else "Create"
    home = str(pathlib.Path.home())
    if filetype == "dir":
      return QtWidgets.QFileDialog.getExistingDirectory(
        self._widgets_window,
        caption,
        home,
        QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks,
      )
    elif filetype == "image":
      filter_str = "Image Files (*.png *.jpg *.bmp)"
    elif filetype == "video":
      filter_str = "Video Files (*.mp4 *.acc)"
    if readonly:
      return QtWidgets.QFileDialog.getOpenFileName(
        self._widgets_window, caption, filter_str
      )

    f, _ = QtWidgets.QFileDialog.getSaveFileName(
      self._widgets_window, caption, home, filter_str
    )
    return f

  def progress_dialog(self, num_steps: int) -> QtWidgets.QProgressDialog:
    dialog = QtWidgets.QProgressDialog(
      "Exporting...", "Cancel", 0, num_steps, self._widgets_window
    )
    return dialog

  def clear_plots(self) -> None:
    self.im_axes.cla()
    self.line_axes.cla()

  @property
  def timer(self):
    return self._timer

  @property
  def sim_prev_button(self) -> QtWidgets.QPushButton:
    return self._widgets_window.sim_prev_button

  @property
  def sim_animate_button(self) -> QtWidgets.QPushButton:
    return self._widgets_window.sim_animate_button

  @property
  def sim_next_button(self) -> QtWidgets.QPushButton:
    return self._widgets_window.sim_next_button

  @property
  def export_button(self) -> QtWidgets.QPushButton:
    return self._widgets_window.export_button

  @property
  def figure(self) -> Figure:
    return self._figure_window._figure.figure

  @property
  def im_axes(self) -> Axes:
    return self._figure_window._plot_axes["image"]

  @property
  def line_axes(self) -> Axes:
    return self._figure_window._plot_axes["plot"]

  def draw(self) -> None:
    self.figure.canvas.draw_idle()

  def show(self) -> None:
    self._figure_window.show()
    self._widgets_window.show()
    self._figure_window.raise_()
    self._widgets_window.raise_()
