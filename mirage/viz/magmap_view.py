from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
from typing import Optional, Union

from mirage.util import DuplexChannel
from mirage.calc.reducers import MagnificationMapReducer, LightCurvesReducer
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

  def show(self, reducer: Union[MagnificationMapReducer, LightCurvesReducer], curve_id: int = 0):  # type: ignore
    if isinstance(reducer, MagnificationMapReducer):
      magnitudes = -2.5 * np.log10(reducer.output)  # type: ignore
      self.img_ax.imshow(magnitudes, cmap=self.colormap)
      # self.curve_ax.plot(x_ax, y_ax)
    self.fig.show()

  @classmethod
  def compatible_reducers(cls):
    return [MagnificationMapReducer]
