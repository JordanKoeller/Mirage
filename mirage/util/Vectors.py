
from astropy import units as u

from .Jsonable import Jsonable

class Vec2D(Jsonable):
    """Class for storing and manipulating 2-dimensional vectors. Internally, this class is based on astropy.units.Quantity. As such, these vectors have dimensions."""
    def __init__(self, x,y, unit:str=None) -> None:
        super(Vec2D, self).__init__()
        if isinstance(x,int) and isinstance(y,int):
            self._quant = u.Quantity([x,y],unit,dtype=int)
        else:
            self._quant = u.Quantity([x,y],unit)

    def to(self,unit):
        quant = self._quant.to(unit)
        return Vec2D.from_quant(quant)

    @property
    def x(self):
        return self._quant[0]

    @property
    def y(self):
        return self._quant[1]

    @property
    def unit(self):
        return self._quant.unit

    @property
    def unit_vector(self):
        return self/self.magnitude

    @property
    def magnitude(self) -> u.Quantity:
        return (self.x*self.x + self.y*self.y)**(0.5)

    def copy(self):
        tmp = self._quant.value.copy()
        return Vec2D(tmp[0],tmp[1],str(self.unit))

    @property 
    def json(self):
        ret = {}
        ret['x'] = self.x.value
        ret['y'] = self.y.value
        ret['unit'] = str(self.unit)
        return ret

    @classmethod
    def from_json(cls,js):
        x = js['x']
        y = js['y']
        un = js['unit']
        return cls(x,y,un)

    @classmethod
    def from_quant(cls,q):
        return Vec2D(q[0].value,q[1].value,q.unit)

    @property
    def quantity(self):
        return self._quant.copy()

    def as_value_tuple(self,unit=None):
        if unit:
            return (self.x.to(unit).value,self.y.to(unit).value)
        else:
            return (self.x.value,self.y.value)

    def __add__(self,other) -> 'Vec2D':
        if isinstance(other,Vec2D):
            x = self.x + other.x
            y = self.y + other.y
            unit = self.unit
            return Vec2D(x.value,y.value,x.unit)
        else:
            return Vec2D.from_quant(self._quant+other)
        # elif isinstance(other,u.Quantity):
        #     other = other.to(self.unit)
        #     return Vec2D((self.x+other).value,(self.y+other).value,(self.x+other).unit)
        # else:
        #     return Vec2D(self.x+other,self.y+other,self.unit)
        # else:
        #     raise ValueError("Needs to be a Vec2D or astropy Quantity")

    def __sub__(self,other) -> 'Vec2D':
        return self + (-other)

    def __neg__(self) -> 'Vec2D':
        return Vec2D(-self.x.value, -self.y.value, self.unit)

    def __mul__(self,other) -> 'Vec2D':
        if isinstance(other,Vec2D):
            return Vec2D.from_quant(self._quant*other._quant)
        else:
            return Vec2D.from_quant(self._quant*other)

    def __truediv__(self,other) -> 'Vec2D':
        if isinstance(other,Vec2D):
            return Vec2D.from_quant(self._quant/other._quant)
        else:
            return Vec2D.from_quant(self._quant/other)
        # if isinstance(other,u.Quantity):
        #     return Vec2D((self.x/other).value,(self.y/other).value,(self.x*other).unit)
        # elif isinstance(other,Vec2D):
        #     q = (self._quant/other._quant)
        #     return Vec2D(q[0].value,q[1].value,self.unit)
        # return Vec2D(self.x.value/other,self.y.value/other,self.unit)

    def __eq__(self,other:'Vec2D') -> bool:
        return (self._quant == other._quant).all()

    def __neq__(self,other:'Vec2D') -> bool:
        return not self == other

    def __repr__(self) -> str:
        x = self.x.value
        y = self.y.value 
        unit = str(self.unit)
        if isinstance(x,int) and isinstance(y,int):
            return "< %d, %d > %s" % (x,y,unit)
        else:
            return "< %.3f, %.3f > %s" % (x,y,unit)


class PolarVec(Jsonable):
    """Polar Representation of a vector"""

    def __init__(self,magnitude, direction, unit=None) -> None:
        """Construct a vector in polar coordinates
        
        Accepts a magnitude and direction for the vector, as well as an optional field for a unit.

        Arguments:

        * `magnitude` may be a float, int, or Quantity.
        * `direction` may be a float, int, or Quantity. If the supplied field is not a Quantity, it is assumed to be in degrees.
        * `unit` (optional) `str` specifiying the dimension of the vector. This argument is only used if the `magnitude` argument is not a Quantity. If `magnitude` is a Quantity, this argument is ignored.
        """ 
        if isinstance(magnitude, u.Quantity):
            self._magnitude = magnitude
        else:
            self._magnitude = u.Quantity(magnitude,unit)
        if isinstance(direction,u.Quantity):
            self._direction = direction.to('rad')
        else:
            self._direction = u.Quantity(direction, 'degree').to('rad')

    @property
    def magnitude(self):
        return self._magnitude

    @property
    def direction(self):
        return self._direction

    @property
    def unit(self):
        return self.magnitude.unit

    def to(self,unit):
        self._magnitude = self.magnitude.to(unit)
        return self

    def __repr__(self):
        return "(R,Degrees) = < %.3f, %.3f > %s" % (self.magnitude.value,self.direction.to('degree').value, self.unit)

    @property
    def json(self):
        ret = {}
        ret['magnitude'] = Jsonable.encode_quantity(self.magnitude)
        ret['direction'] = self.direction.to('degree').value
        return ret 

    @classmethod
    def from_json(cls,js):
        mag = Jsonable.decode_quantity(js['magnitude'])
        direction = js['direction']
        return cls(mag,direction)
    
    