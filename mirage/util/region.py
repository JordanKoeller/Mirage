from dataclasses import dataclass
from typing import Optional, List, Self, Union, Tuple
from functools import cached_property

from astropy import units as u
import numpy as np

from mirage.util import Vec2D


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

  def to(self, unit: Union[str, u.Unit]) -> Self:
    return PixelRegion(  # type: ignore
        dims=self.dims.to(unit),
        center=self.center.to(unit) if self.center else None,
        resolution=self.resolution,
    )

  def subdivide(self, parallelism_factor: int) -> List[Self]:
    return [self]

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
