from .reducer import LensReducer, QueryAccumulator

from .Registry import ReducerRegistry

from .magmap_reducer import MagmapReducer, MagnificationQuery

class ReducerTransporter:

    def __init__(self, klass, transport):
        self.transport = transport
        self.klass = klass

    @staticmethod
    def from_reducer(reducer):
        return ReducerTransporter(type(reducer), reducer.transport())

    def get_reducer(self):
        return self.klass.from_transport(self.transport)