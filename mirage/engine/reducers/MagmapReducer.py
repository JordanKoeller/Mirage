from __future__ import annotations


from astropy import units as u
import numpy as np

from typing import TypeVar, Generic, Iterator, Tuple


from .ReducerInterfaces import QueryReducer
from ...util.Region import PixelRegion
from .MagnificationQuery import MagnificationQuery
from .Registry import ReducerRegistry


@ReducerRegistry.register
class MagmapReducer(QueryReducer[Tuple[int, int], np.int64], ABC):

    def __init__(self, region: PixelRegion, radius: u.Quantity):
        self._region = region
        self._radius = radius
        self._storage = None

    def merge(self, other):
        if not (self.populated and other.populated):
            raise ValueError("One of the storages was empty.")
        ret = MagmapReducer(self._region, self._radius)
        ret._storage = self._storage + other._storage
        return ret

    def query_points(self) -> Iterator[MagnificationQuery]:
        self._storage = np.zeros(self._region.resolution.as_value_tuple(), dtype=np.int32)
        pixels = self._region.pixels.value
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                yield MagnificationQuery((i, j), pixels[i,j,0], pixels[i,j,1], self._radius.value)
    
    def save_value(self, query_id: Tuple[int, int], value: np.int64) -> None:
        i, j = query_id
        self._storage[i, j] = value

    def clone_empty(self) -> MagmapReducer:
        return MagmapReducer(self._region, self._radius)

    @property
    def value(self) -> np.ndarray:
        return self._storage

    @property
    def populated(self):
        return self._storage is not None

    @staticmethod
    def identifier() -> str:
        return "magmap"
