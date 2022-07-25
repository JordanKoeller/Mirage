from __future__ import annotations


from astropy import units as u
import numpy as np

from typing import TypeVar, Generic, Iterator, Tuple
from abc import ABC

from mirage.util import PixelRegion

from .reducer import LensReducer, QueryAccumulator

# from .ReducerInterfaces import QueryReducer
# from .MagnificationQuery import MagnificationQuery
# from .Registry import ReducerRegistry

class MagnificationQuery(QueryAccumulator):

    def __init__(self, identifier: Q, x: float, y: float, radius: float):
        self.x = x
        self.y = y
        self.radius = radius
        # QueryAccumulator.__init__(self, identifier, x, y, radius)
        self._count = 0

    def reduce_ray(self, ray):
        self._count += 1
    
    def get_result(self):
        return float(self._count)

class MagmapReducer(LensReducer):

    def __init__(self, region: PixelRegion, radius: u.Quantity):
        self._region = region
        self._radius = radius
        self._storage = None
        self.i = None
        self.j = None
        self.active_key = None

    def merge(self, other):
        if not (self.populated and other.populated):
            raise ValueError("One of the storages was empty.")
        ret = MagmapReducer(self._region, self._radius)
        ret._storage = self._storage + other._storage
        return ret

    def start_iteration(self):
        self.i = 0
        self.j = 0
        self._storage = np.zeros(self._region.resolution.as_value_tuple(), dtype=np.float64)
        self.pixels = self._region.pixels.value

    def has_next_accumulator(self):
        return self._storage is None or self.i == self._storage.shape[0]

    def next_accumulator(self):
        ret = MagnificationQuery((self.i, self.j), self.pixels[self.i,self.j, 0], self.pixels[self.i,self.j,1], self._radius.value)
        self.active_key = (self.i, self.j)
        self.j += 1
        if self.j == self._storage.shape[1]:
            self.i += 1
            self.j = 0
        return ret


    def save_value(self, value: np.int64) -> None:
        # i, j = query_id
        self._storage[self.active_key[0], self.active_key[1]] = value

    def clone_empty(self) -> MagmapReducer:
        return MagmapReducer(self._region, self._radius)

    def value(self) -> np.ndarray:
        return self._storage

    @property
    def populated(self):
        return self._storage is not None

    @staticmethod
    def identifier() -> str:
        return "magmap"
