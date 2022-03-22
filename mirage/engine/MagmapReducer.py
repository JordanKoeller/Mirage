from astropy import units as u
import numpy as np

from .QueryReducer import QueryReducer
from ..util.Region import PixelRegion


class MagmapReducer(QueryReducer):

    def __init__(self, region: PixelRegion, radius: u.Quantity):
        self._region = region
        self._radius = radius
        self._storage = None

    def merge(self, other):
        if not (self.populated and other.populated):
            raise ValueError("One of the storages was empty.")
        ret = MagmapReducer(self._region, self._radius)
        ret.set_storage(self._storage + other._storage)
        return ret

    def query_points(self):
        self._storage = np.ndarray(self._region.resolution.as_value_tuple(), dtype=np.int32)
        pixels = self._region.pixels.value
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                yield (i, j), (pixels[i,j], self._radius.value)
    
    def set_query_magnitude(self, query_id, value):
        i, j = query_id
        self._storage[i, j] = value

    @property
    def value(self):
        return self._storage

    @property
    def populated(self):
        return self._storage != None