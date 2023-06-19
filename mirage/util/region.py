from dataclasses import dataclass
from typing import Optional, List, Self, Union, Tuple
from functools import cached_property

from astropy import units as u
import numpy as np

from mirage.util import Vec2D, Index2D


@dataclass(kw_only=True, frozen=True)
class Region:
  """
  Describes a two-dimensional region.

  Args:

    + dims (Vec2D): The (width, height) of the region
    + center (Vec2D): The position vector for the center of the region. Default (0, 0).
  """

  dims: Vec2D
  center: Optional[Vec2D] = None

  def to(self, unit: Union[str, u.Unit]) -> Self:
    return Region(  # type: ignore
        dims=self.dims.to(unit),
        center=self.center.to(unit) if self.center else None,
    )

  def pixellate(self, resolution: Vec2D) -> "PixelRegion":
    return PixelRegion(dims=self.dims, center=self.center, resolution=resolution)

  @property
  def unit(self) -> u.Unit:
    return self.dims.unit

  @property
  def area(self) -> u.Quantity:
    return self.dims.x * self.dims.y

  @property
  def outline(self) -> u.Quantity:
    center: Vec2D = (
        self.center.to(self.unit) if self.center else Vec2D.zero_vector(self.unit)
    )
    tl = (center - self.dims / 2.0).to(self.unit)  # type: ignore
    br = (center + self.dims / 2.0).to(self.unit)  # type: ignore
    data = [
        [tl.x.value, tl.y.value],
        [br.x.value, tl.y.value],
        [br.x.value, br.y.value],
        [tl.x.value, br.y.value],
        [tl.x.value, tl.y.value],
    ]
    return u.Quantity(np.array(data), self.unit)

  @property
  def span(self) -> Tuple[Vec2D, Vec2D]:
    center: Vec2D = (
        self.center.to(self.unit) if self.center else Vec2D.zero_vector(self.unit)
    )
    tl = (center - self.dims / 2.0).to(self.unit)  # type: ignore
    br = (center + self.dims / 2.0).to(self.unit)  # type: ignore
    return tl, br


@dataclass(kw_only=True, frozen=True)
class PixelRegion(Region):
  """
  Describes a pixelated region. Or in other words a grid.

  Args:

    + dims (Vec2D): The (height, width) of the region.
    + center (Vec2D): The position vector for the center of the region. Default (0, 0).
    + resolution (Vec2D): The resolution of the pixel region (h x w).
  """

  resolution: Vec2D

  @classmethod
  def from_span(cls, min_corner: Vec2D, max_corner: Vec2D, resolution: Vec2D) -> Self:
    """
    Constructs a PixelRegion given the top left corner, bottom right corner, and
    resolution of the grid.

    Note that the min and max corners represent actual pixel locations - not the
    bounding box of the region

    Args:

      + min_corner (Vec2D) - The top left corner of the PixelRegion
      + max_corner (Vec2D) - The bottom right corner of the PixelRegion
      + resolution (Vec2D) - The resolution of the PixelRegion. Should be unitless
    """
    min_corner = min_corner.to(max_corner.unit)

    center = (min_corner + max_corner) / 2
    delta = (max_corner - min_corner).div(resolution - Vec2D.unitless(1, 1))
    dims = max_corner - min_corner + delta

    return cls(dims=dims, center=center, resolution=resolution)  # type: ignore

  def to(self, unit: Union[str, u.Unit]) -> Self:
    return PixelRegion(  # type: ignore
        dims=self.dims.to(unit),
        center=self.center.to(unit) if self.center else None,
        resolution=self.resolution,
    )

  def subdivide(self, region_count: int) -> List[Self]:
    """
    Subdivide `self` into a grid of sub-regions.

    The subregions, all merged together, produce an identical set of pixels as the
    original region.

    Notes:

      + If `region_count` cannot easily factor into two whole numbers, the closest pair
        of whole numbers (rounded down) will be used. In other words, it is better to
        think of `region_count` as an upper limit to the number of subregions, instead
        of the exact number of subregions.
      + The number of pixels in a subregion may vary by +/- 1 row and +/- 1 column. In
        other words, a set of subregions of resolutions ranging from (99, 99) to
        (101, 101) is expected. That being said, all subregions are always congruent.
        Just depending on where the subregion boundaries "line up" with the
        pixel grid, the nuber of pixels within a subregion may vary by +/- 1 rows/columns.

    Args:

      + region_count (int): The number of subregions to create

    Returns:
      + List[PixelRegion] The produced regions in a list of `region_count` length
    """
    w, h = PixelRegion._find_closest_divisors(region_count)
    supergrid_resolution = Vec2D.unitless(w, h)
    grid_float_index_dims = self.resolution.div(supergrid_resolution)
    x_indices = [(0, np.floor(grid_float_index_dims.x.value - 1))]
    y_indices = [(0, np.floor(grid_float_index_dims.y.value - 1))]
    for x_i in range(1, w):
      _, prev_e = x_indices[x_i - 1]
      curr_s = prev_e + 1
      curr_e = min(
          self.resolution.x.value - 1,
          np.floor(grid_float_index_dims.x.value * (x_i + 1)),
      )
      x_indices.append((curr_s, curr_e))

    for y_i in range(1, h):
      _, prev_e = y_indices[y_i - 1]
      curr_s = prev_e + 1
      curr_e = min(
          self.resolution.y.value - 1,
          np.floor(grid_float_index_dims.y.value * (y_i + 1)),
      )
      y_indices.append((curr_s, curr_e))

    x_indices[-1] = (x_indices[-1][0], self.resolution.x.value - 1)
    y_indices[-1] = (y_indices[-1][0], self.resolution.y.value - 1)

    subgrids: List[PixelRegion] = []
    for x_i in range(w):
      for y_i in range(h):
        s_x, e_x = x_indices[x_i]
        s_y, e_y = y_indices[y_i]
        subgrid_resolution = Vec2D.unitless(e_x - s_x + 1, e_y - s_y + 1)
        subgrid_min_corner = self[Index2D(s_x, s_y)]
        subgrid_max_corner = self[Index2D(e_x, e_y)]
        subgrids.append(
            PixelRegion.from_span(
                subgrid_min_corner, subgrid_max_corner, subgrid_resolution
            )
        )

    return subgrids  # type: ignore

  def __getitem__(self, index: Index2D):
    if index.x > self.resolution.x.value or index.y > self.resolution.y.value:
      raise ValueError(
          f"{index=} out of bounds for PixelRegion of resolution {self.resolution}"
      )

    center = self.center.to(self.unit) if self.center else Vec2D.zero_vector(self.unit)
    low_limit = center - self.dims / 2
    high_limit = center + self.dims / 2
    min_corner = (low_limit + self.delta / 2).to(self.unit)  # type: ignore

    return Vec2D(
        min_corner.x + self.delta.x * index.x,
        min_corner.y + self.delta.y * index.y,
        self.unit,
    )

  @property
  def delta(self) -> Vec2D:
    return self.dims.div(self.resolution)

  @cached_property
  def pixels(self) -> u.Quantity:
    """
    Get the pixel grid for this :class:`PixelRegion`

    Note: When constructing the pixel coordinates, the center of each pixel's coordinate is used.
    """
    center = self.center.to(self.unit) if self.center else Vec2D.zero_vector(self.unit)

    low_limit = center - self.dims / 2
    high_limit = center + self.dims / 2
    coords_start = (low_limit + self.delta / 2).to(self.unit)  # type: ignore
    coords_end = (high_limit - self.delta / 2).to(self.unit)  # type: ignore

    x_ax = np.linspace(
        coords_start.x.value, coords_end.x.value, int(self.resolution.x.value)
    )
    y_ax = np.linspace(
        coords_start.y.value, coords_end.y.value, int(self.resolution.y.value)
    )

    x, y = np.meshgrid(x_ax, y_ax)
    grid = np.stack([x, y], 2)
    return u.Quantity(grid, self.unit)

  @staticmethod
  def _find_closest_divisors(n: int) -> Tuple[int, int]:
    rover = int(np.round(np.sqrt(n)))
    while n % rover != 0:
      rover -= 1
    return int(rover), int(n // int(rover))
