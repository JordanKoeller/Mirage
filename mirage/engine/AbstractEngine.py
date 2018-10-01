from mirage.parameters import Parameters

import numpy as np

class EngineHandler(object):

    def __init__(self,engine):
        self._calculation_delegate = engine
        self._parameters = None

    @property
    def calculation_delegate(self):
        return self._calculation_delegate

    def update_parameters(self,params:Parameters,force_recalculate=False) -> bool:
        if not self._parameters or force_recalculate or not self._parameters.is_similar(params):
            self._parameters = params
            print("Recalculating")
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