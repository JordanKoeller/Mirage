from typing import Self, Optional
from dataclasses import dataclass

from mirage.calc import Reducer, KdTree
from mirage.calc.reducer_funcs import populate_magmap
from mirage.util import Vec2D, PixelRegion, DelegateRegistry
from mirage.model import SourcePlane

import numpy as np
from astropy import units as u

HIT_COLOR = np.array([120, 120, 255])


@dataclass
@DelegateRegistry.register
class LensedImageReducer(Reducer):
  query: Vec2D
  radius: u.Quantity

  def __post_init__(self) -> None:
    self.canvas: Optional[np.ndarray] = None

  def reduce(self, traced_rays: KdTree, _source_plane: Optional[SourcePlane]):
    inds = traced_rays.query(self.query.to("theta_0"), self.radius.to("theta_0"))
    canvas_shape = (traced_rays.data_shape[0], traced_rays.data_shape[1], 3)
    self.canvas = np.zeros(canvas_shape, dtype=np.uint8)
    for i, j in inds:
      self.canvas[i, j] = HIT_COLOR

  def merge(self, other: Self):
    other_canvas = other.output
    if self.canvas is not None and other_canvas is not None:
      self.canvas[other_canvas[:, :, 0] == HIT_COLOR[0]] = HIT_COLOR
    elif other_canvas is not None:
      self.canvas = other_canvas

  @property
  def output(self) -> Optional[np.ndarray]:
    if self.canvas is not None:
      return np.copy(self.canvas)
    return None


@dataclass
@DelegateRegistry.register
class MagnificationMapReducer(Reducer):
  radius: u.Quantity
  resolution: Vec2D
  canvas: Optional[np.ndarray]

  def reduce(self, traced_rays: KdTree, source_plane: Optional[SourcePlane]):
    if not source_plane:
      raise ValueError("Reducer did not have a source_plane instance")
    pixel_region = PixelRegion(
        dims=source_plane.source_region.to("theta_0").dims,
        center=source_plane.source_region.to("theta_0").center,
        resolution=self.resolution,
    )

    pixels = pixel_region.to("theta_0").pixels.value
    radius = self.radius.to("theta_0").value

    self.canvas = populate_magmap(pixels, radius, traced_rays)

  def merge(self, other: Self):
    other_canvas = other.output
    if self.canvas is not None and other_canvas is not None:
      self.canvas += other_canvas
    elif other_canvas is not None:
      self.canvas = other_canvas

  @property
  def output(self) -> Optional[np.ndarray]:
    if self.canvas is not None:
      return np.copy(self.canvas)
    return None
