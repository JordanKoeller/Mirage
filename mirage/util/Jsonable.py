from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod

from astropy.units import Quantity

class Jsonable(ABC):
    """Abstract base class for objects that have methods for converting to and from
    JSON representations."""
    def __init__(self):
        pass

    @abstractproperty
    def json(self):
        pass

    @abstractclassmethod
    def from_json(cls,js):
        pass

    @staticmethod
    def encode_quantity(quant:Quantity) -> 'Dict':
        ret = {}
        if isinstance(quant.value,int) or isinstance(quant.value,float):
            ret['values'] = quant.value
        else:
            ret['values'] = quant.value.tolist()
        ret['unit'] = str(quant.unit)
        return ret

    @staticmethod
    def decode_quantity(js:'Dict') -> Quantity:
         values = js['values']
         unit = js['unit']
         return Quantity(values,unit)
        

    #Method template



    # @property 
    # def json(self):

    # @classmethod
    # def from_json(cls,js):
