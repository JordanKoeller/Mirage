from .Vectors import Vec2D
from .Jsonable import Jsonable

from astropy import units as u
import numpy as np

import math

class Region(Jsonable):

    """Defines a region of space.
    
    The region is rectangular, with a center and dimensions specified.
    """ 

    def __init__(self,center:Vec2D, dims:Vec2D) -> None:
        self._center = center
        self._dims = dims.to(center.unit)

    def to(self,unit:str):
        self._center = self._center.to(unit)
        self._dims = self._dims.to(unit)
        return self


    @property
    def center(self) -> Vec2D:
        return self._center

    @property
    def dimensions(self) -> Vec2D:
        return self._dims

    @property
    def area(self) -> u.Quantity:
        return self.dimensions.x*self.dimensions.y

    def json_helper(self) -> dict:
        ret = {}
        ret['center'] = self.center.json
        ret['dims'] = self.dimensions.json
        return ret
        

    @property
    def json(self) -> dict:
        return self.json_helper()

    @classmethod
    def from_json(cls,js):
        center = Vec2D.from_json(js['center'])
        dims = Vec2D.from_json(js['dims'])
        return cls(center,dims)

    def __repr__(self):
        return "Center= %s, Dimensions = %s" % (str(self.center),str(self.dimensions))

class CircularRegion(object):

    def __init__(self,center:Vec2D, radius:u.Quantity):
        self._center = center
        self._radius = radius.to(center.unit)

    @property
    def center(self):
        return self._center
    @property
    def radius(self):
        return self._radius
    
    @property
    def area(self):
        return math.pi*self.radius**2

    def random_sample(self,num_points=1,rng=None):
        rng = rng or np.random
        r = np.sqrt(np.random.rand((num_points)))
        theta = np.random.rand(num_points) * np.pi*2
        ret = np.ndarray((num_points,2))
        ret[:,0] = self.radius.value*np.cos(theta)*r
        ret[:,1] = self.radius.value*np.sin(theta)*r
        return u.Quantity(ret,self.radius.unit)

    def to(self,unit):
        self._center = self._center.to(unit)
        self._radius = self._radius.to(unit)
        return self


    
class PixelRegion(Region):

    def __init__(self,center:Vec2D,dims:Vec2D,pixels:Vec2D) -> None:
        Region.__init__(self,center,dims)
        self._resolution = Vec2D(int(pixels.x),int(pixels.y))

    @property
    def dTheta(self) -> Vec2D:
        ret = self.dimensions/self.resolution
        return ret

    @property
    def resolution(self) ->Vec2D:
        return self._resolution

    @property
    def pixels(self) -> u.Quantity:
        print("NOTE: pixels function on PixelRegion may be incorrect")
        self.to(self.center.unit)
        # grid = np.ndarray((int(self.resolution.x),int(self.resolution.y),2))
        x_ax = np.linspace((self.center.x - self.dimensions.x/2).value,(self.center.x + self.dimensions.x/2).value,self.resolution.x.value)
        y_ax = np.linspace((self.center.y - self.dimensions.y/2).value,(self.center.y + self.dimensions.y/2).value,self.resolution.y.value)
        x,y = np.meshgrid(x_ax,y_ax)
        grid = np.stack([x,y],2)
        # for i in range(grid.shape[0]):
        #     for j in range(grid.shape[1]):
        #         grid[i,j,0] = (self.center.x + self.dTheta.x*(i - self.resolution.x.value/2)).value
        #         grid[i,j,1] = (self.center.y + self.dTheta.y*(j - self.resolution.y.value/2)).value
        return u.Quantity(grid,self.center.unit)
    


    def loc_to_pixel(self,loc:Vec2D) -> Vec2D:
        delta = loc - self.center
        pixellated = delta.to(self.dTheta.unit)/self.dTheta
        print(pixellated)
        print(self.resolution/2)
        shift = pixellated + self.resolution/2
        return Vec2D(int(shift.x.value),int(shift.y.value))

    def pixel_to_loc(self,pixel:Vec2D) -> Vec2D:
        shiftp = pixel - self.resolution/2
        delta = self.dTheta*shiftp
        return delta + self.center.to(delta.unit)


    @property
    def json(self):
        ret = Region.json_helper(self)
        ret['resolution'] = self.resolution.json
        return ret

    @classmethod
    def from_json(cls,js):
        center = Vec2D.from_json(js['center'])
        dims = Vec2D.from_json(js['dims'])
        resolution = Vec2D.from_json(js['resolution'])
        return cls(center,dims,resolution)

    def __repr__(self):
        return "Center= %s, Dimensions = %s, Resolution = %s" % (str(self.center),str(self.dimensions), str(self.resolution))

class _IntVect(Vec2D):

    def __init__(self,x,y):
        Vec2D.__init__(self,x,y)
        self._quant = u.Quantity([x,y],unit='',dtype=np.int)

    @property
    def __repr__(self):
        return "<%d, %d>" % (self.x, self.y)
