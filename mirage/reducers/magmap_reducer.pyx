# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

import numpy
cimport numpy as np

from mirage.reducers.reducer cimport LensReducer, QueryAccumulator, Query

cdef class MagnificationQuery(QueryAccumulator):

    def __init__(self, double x, double y, double radius):
        self.query = Query(x, y, radius)
        self.count = 0.0

    cpdef void reduce_ray(self, const double[:] ray):
        self.count += 1.0

    cpdef double get_result(self):
        return self.count

    cpdef Query query_point(self):
        return self.query

cdef class MagmapReducer(LensReducer):

    def __init__(self, object region, double radius):
        self.radius = radius
        self.region = region
        self.storage = None
        self.active_key = None
        self.ij = None
        pixels = self.region.pixels.value
        self.pixels = pixels
        active_key = numpy.array([0, 0], dtype=numpy.int32)
        ij = numpy.array([0, 0], dtype=numpy.int32)
        self.active_key = active_key
        self.ij = ij

    cpdef LensReducer merge(self, LensReducer other):
        cdef LensReducer ret = MagmapReducer(self.region, self.radius)
        s_a = numpy.array(self.storage)
        s_b = numpy.array(other.storage)
        s_sum = s_a + s_b
        ret.storage = s_sum
        return ret

    cpdef void start_iteration(self):
        storage = numpy.zeros(self.region.resolution.as_value_tuple(), dtype=numpy.float64)
        active_key = numpy.array([0, 0], dtype=numpy.int32)
        ij = numpy.array([0, 0], dtype=numpy.int32)
        self.storage = storage
        self.active_key = active_key
        self.ij = ij

    cpdef bint has_next_accumulator(self):
        return self.ij[0] != self.storage.shape[0]

    cpdef MagnificationQuery next_accumulator(self):
        cdef MagnificationQuery ret = MagnificationQuery(
            self.pixels[self.ij[0], self.ij[1], 0], 
            self.pixels[self.ij[0], self.ij[1], 1],
            self.radius)
        self.active_key[0] = self.ij[0]
        self.active_key[1] = self.ij[1]
        self.ij[1] += 1
        if self.ij[1] == self.storage.shape[1]:
            self.ij[0] += 1
            self.ij[1] = 0
        return ret
    
    cpdef void save_value(self, double value):
        self.storage[self.active_key[0], self.active_key[1]] = value

    cpdef MagmapReducer clone_empty(self):
        return MagmapReducer(self.region, self.radius)

    cpdef object value(self):
        ret = numpy.array(self.storage, copy=True)
        return ret

    @staticmethod
    def identifier() -> str:
        return "magmap"

    @property
    def started(self):
        return self.ij is not None

    # cdef'd classes arent very good over the wire, so I decouple the state
    # from the optimized code to use when serializing

    cpdef transport(self):
        ret = {
            "region": self.region,
            "radius": self.radius,
            "ij": numpy.array(self.ij),
            "active_key": numpy.array(self.active_key),
        }
        if self.storage is not None:
            ret['storage'] = numpy.array(self.storage)
        return ret

    @classmethod
    def from_transport(cls, transport):
        ret = cls(transport['region'], transport['radius'])
        ret.ij = transport['ij']
        ret.active_key = transport['active_key']
        if 'storage' in transport:
            ret.storage = transport['storage']
        return ret
    