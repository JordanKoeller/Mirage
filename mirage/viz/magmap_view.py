from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np

from mirage.util import DuplexChannel
from mirage.calc.reducers import MagnificationMapReducer
from mirage.viz import Viz


@Viz.register
class MagmapView(Viz):

  def __init__(self):
    self.fig = plt.figure()
    self.colormap = plt.get_cmap("RdBu")
    self.gridspec = GridSpec(2, 1, figure=self.fig, height_ratios=[1, 5])
    self.curve_ax = self.fig.add_subplot(self.gridspec[0, 0])
    self.img_ax = self.fig.add_subplot(self.gridspec[1, 0])
    self.img_ax.set_axis_off()
    self.img_ax.set_frame_on(True)
    self.fig.set_tight_layout(True)

  def show(self, magmap_reducer: MagnificationMapReducer):  # type: ignore
    magnitudes = -np.log10(magmap_reducer.output)  # type: ignore
    self.img_ax.imshow(magnitudes, cmap=self.colormap)
    self.fig.show()

  @classmethod
  def compatible_reducers(cls):
    return [MagnificationMapReducer]
