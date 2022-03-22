from numpy import integer
def zero_vector(unit=None):
    return Vec2D(0.0,0.0,unit)


def as_primative(value):
    if isinstance(value, integer):
        return int(value)
    else:
        return float(value)


from .Jsonable import Jsonable
from .Vectors import Vec2D, PolarVec
from .Region import Region, PixelRegion, CircularRegion
from .Timing import StopWatch