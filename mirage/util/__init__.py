from numpy import integer
def zero_vector(unit=None):
    return Vec2D(0.0,0.0,unit)


def as_primative(value):
    if isinstance(value, integer):
        return int(value)
    else:
        return float(value)

# A handful of useful functions are defined below

def lerp(a1, b1, value, a2, b2):
    """
    Given `value` in range `[a1, b1]`, linearly interpolate it to be in the range `[a2, b2]`.
    """
    fraction = (value - a1) / (b1 - a1)
    return fraction * (b2 - a1) + a2


from .Jsonable import Jsonable
from .Vectors import Vec2D, PolarVec
from .Region import Region, PixelRegion, CircularRegion
from .Timing import StopWatch