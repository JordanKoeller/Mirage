from .Jsonable import Jsonable
from .Region import CircularRegion, PixelRegion, Region
from .Vectors import PolarVec, Vec2D


def zero_vector(unit=None):
  return Vec2D(0.0, 0.0, unit)
