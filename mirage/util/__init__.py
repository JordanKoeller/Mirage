from .Jsonable import Jsonable

from .Vectors import Vec2D, PolarVec

from .Region import Region, PixelRegion, CircularRegion

def zero_vector(unit=None):
    return Vec2D(0.0,0.0,unit)
