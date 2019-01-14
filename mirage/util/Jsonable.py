from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod

from astropy.units import Quantity

class Jsonable(ABC):
    """Abstract base class for objects that have methods for converting to and from JSON representations."""
    def __init__(self):
        pass

    @abstractproperty
    def json(self):
        pass

    @abstractclassmethod
    def from_json(cls,js):
        pass

    def __repr__(self):
        return str(self.json)

    @staticmethod
    def encode_quantity(quant:Quantity) -> 'Dict':
        """convenience function for converting an :class:`astropy.units.Quantity` instance into a JSON representation.
        """
        ret = {}
        if isinstance(quant.value,int) or isinstance(quant.value,float):
            ret['values'] = quant.value
        else:
            ret['values'] = quant.value.tolist()
        ret['unit'] = str(quant.unit)
        return ret

    @staticmethod
    def decode_quantity(js:'Dict') -> Quantity:
        """
        method for constructing a :class:`astropy.units.Quantity` from a JSON representation.
        """
        values = js['values']
        unit = js['unit']
        return Quantity(values,unit)
        

    #Method template



    # @property 
    # def json(self):

    # @classmethod
    # def from_json(cls,js):
