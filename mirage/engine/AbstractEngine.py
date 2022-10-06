from mirage.parameters import Parameters
from mirage.util import Vec2D

from astropy import units as u
import numpy as np

class EngineHandler(object):

    def __init__(self,engine):
        self._calculation_delegate = engine
        self._parameters = None

    @property
    def calculation_delegate(self):
        return self._calculation_delegate

    @property
    def parameters(self):
        return self._parameters
    

    def update_parameters(self,params:Parameters,force_recalculate=False) -> bool:
        if not self._parameters or force_recalculate or not self._parameters.is_similar(params):
            self._parameters = params
            self.calculation_delegate.reconfigure(self._parameters)
            return True
        else:
            self._parameters = params
            print("Could skip recalculation")
            return False

    def query_points(self,*args,**kwargs):
        ret = self.calculation_delegate.query_points(*args,**kwargs)
        rb = self._parameters.raw_brightness
        if ret.dtype == object:
            for i in range(ret.shape[0]):
                ret[i] = np.array(ret[i])/rb
            return ret
        else:
            return ret/rb

    def query_region(self,*args,**kwargs):
        ret = self.calculation_delegate.query_region(*args,**kwargs)
        print(ret.max())
        rb = self._parameters.raw_brightness
        return ret/rb

    def query_caustics(self,*args,**kwargs):
        return self.calculation_delegate.query_caustics(*args,**kwargs)

    def get_pixels(self,location:Vec2D,radius:u.Quantity) -> np.ndarray:
        return self.calculation_delegate.get_connecting_rays(location,radius)

    def query(self, reducer):
        return self.calculation_delegate.query(reducer)
