from typing import Self, Optional, List
from dataclasses import dataclass

from mirage.calc import Reducer, KdTree
from mirage.calc.reducer_funcs import populate_magmap, populate_lightcurve
from mirage.util import Vec2D, PixelRegion, DelegateRegistry, Region
from mirage.model import SourcePlane

import numpy as np
from astropy import units as u

HIT_COLOR = np.array([120, 120, 255])


@DelegateRegistry.register
@dataclass(kw_only=True)
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


@DelegateRegistry.register
@dataclass(kw_only=True)
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
    other_canvas = other.canvas
    if self.canvas is not None and other_canvas is not None:
      self.canvas += other_canvas
    elif other_canvas is not None:
      self.canvas = other_canvas

  @property
  def output(self) -> Optional[np.ndarray]:
    if self.canvas is not None:
      return np.copy(self.canvas)
    return None


@DelegateRegistry.register
@dataclass(kw_only=True)
class LightCurvesReducer(Reducer):
  radius: u.Quantity
  resolution: u.Quantity  # In units of N/dist or dist
  num_curves: int
  seed: Optional[int]

  def __post_init__(self):
    self._curves: List[np.ndarray] = [np.array([]) for _ in range(self.num_curves)]

  def reduce(self, traced_rays: KdTree, source_plane: Optional[SourcePlane]):
    if not source_plane:
      raise ValueError("Reducer did not have a source_plane instance")
    query_points = self.get_query_points(source_plane.source_region)
    radius = self.radius.to("theta_0").value
    for i in range(self.num_curves):
      queries = query_points[i].to("theta_0").value
      self._curves[i] = populate_lightcurve(queries, radius, traced_rays)

  def merge(self, other: Self):
    for i in range(self.num_curves):
      if self._curves[i] is not None and other._curves[i] is not None:
        self._curves[i] = self._curves[i] + other._curves[i]
      elif other._curves[i] is not None:
        self._curves[i] = other._curves[i]

  @property
  def output(self):
    return self._curves

  def get_query_points(self, region: Region) -> List[u.Quantity]:
    """
    Returns a list of fully interpolated, randomly generated query points, where each
    element of the list is all the query points for a single light curve.
    """
    lines = []
    query_seeds = self.get_query_seeds(region)
    diff = self.resolution
    if u.get_physical_type(self.resolution) == u.get_physical_type((1.0 / query_seeds)):
      diff = 1.0 / self.resolution
    diff = diff.to(region.unit)
    for i in range(self.num_curves):
      x0, y0, x1, y1 = query_seeds[i]
      direction = (Vec2D(x1, y1) - Vec2D(x0, y0)).direction
      xs = np.arange(x0.value, x1.value, direction.x.value * diff.value)
      ys = np.arange(y0.value, y1.value, direction.y.value * diff.value)
      num_pts = min(xs.size, ys.size)
      line: np.ndarray = np.ndarray((num_pts, 2))
      line[:, 0] = xs[:num_pts]
      line[:, 1] = ys[:num_pts]
      lines.append(u.Quantity(line, region.unit))
    return lines

  def get_query_seeds(self, region: Region) -> u.Quantity:
    """
    Generate all the query points for this reducer.

    generates two random coordinates in the lens plane `num_curves` many times,
    connects them with a line, then interpolates them onto a bounding box of [-0.5, 0.5].
    """
    rng = np.random.default_rng(self.seed)
    points = rng.random((self.num_curves, 4))
    dx = points[:, 2] - points[:, 0]
    dy = points[:, 3] - points[:, 1]
    ms = dy / dx
    ps = points[:, :2]
    # y - y1 = m(x - x1)
    # y = m(x - x1) + y1
    # y = mx - mx1 + y1
    # Thus, b = (-m*x1 + y1).
    y0s = -ms * ps[:, 0] + ps[:, 1]  # y at x = 0
    # letting y = 0, 0 = mx + b ==> -b/m = x
    x0s = -y0s / ms  # x at y = 0
    y1s = ms + y0s  # y at x = 1
    # letting y = 1, 1 = mx + b ==> 1 - b = mx ==> (1 - b) / m = x
    x1s = (1 - y0s) / ms
    rows = []
    e = 1e-6  # tolerance
    for i in range(self.num_curves):
      row = []
      if y0s[i] <= (1.0 + e) and y0s[i] >= (0.0 - e):
        row.extend([0.0, y0s[i]])
      if x0s[i] <= (1.0 + e) and x0s[i] >= (0.0 - e):
        row.extend([x0s[i], 0.0])
      if y1s[i] <= (1.0 + e) and y1s[i] >= (0.0 - e):
        row.extend([1.0, y1s[i]])
      if x1s[i] <= (1.0 + e) and x1s[i] >= (0.0 - e):
        row.extend([x1s[i], 1.0])
      rows.append(row)
    centered_points = np.array(rows) - 0.5
    center = (
        region.center if region.center is not None else Vec2D.zero_vector(region.unit)
    )
    scaled_points: np.ndarray = np.ndarray((self.num_curves, 4))
    scaled_points[:, 0] = centered_points[:, 0] * region.dims.x.value + center.x.value
    scaled_points[:, 1] = centered_points[:, 1] * region.dims.y.value + center.y.value
    scaled_points[:, 2] = centered_points[:, 2] * region.dims.x.value + center.x.value
    scaled_points[:, 3] = centered_points[:, 3] * region.dims.y.value + center.y.value
    return u.Quantity(scaled_points, region.unit)
