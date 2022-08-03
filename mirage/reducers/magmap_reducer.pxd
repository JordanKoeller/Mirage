# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

import numpy
cimport numpy as np
from mirage.reducers.reducer cimport LensReducer, QueryAccumulator, Query

cdef class MagnificationQuery(QueryAccumulator):

    cdef:
        Query query
        double count
    """
    Ingest in a ray and add it to the accumulator
    """
    cpdef void reduce_ray(self, const double[:] ray)

    """
    Return the final accumulator value
    """
    cpdef double get_result(self)

    cpdef Query query_point(self)


cdef class MagmapReducer(LensReducer):
    cdef:
        object region
        double radius
        # np.ndarray[np.float64_t, ndim=2] storage
        public double[:,:] storage
        # np.ndarray[np.int32_t, ndim=1] ij
        public int[:] ij
        # np.ndarray[np.int32_t, ndim=1] active_key
        public int[:] active_key
        # np.ndarray[np.float64_t, ndim=3] pixels
        public double[:,:, :] pixels
    """
    Merge this reducer with another of the same type.
    """
    cpdef LensReducer merge(self, LensReducer other)

    """
    Create a copy of this LensReducer that is empty with no
    values saved in it yet.
    """
    cpdef MagmapReducer clone_empty(self)

    """
    Given a key and value, save off the value to 
    the reducer.
    """
    cpdef void save_value(self, double value)

    """
    Returns the enclosed value of this reducer.

    This typically returns a numpy array.
    """
    cpdef object value(self)

    """
    Set up internal iterator to start iterating query points
    """
    cpdef void start_iteration(self)

    """
    Advance iteration
    """
    cpdef MagnificationQuery next_accumulator(self)

    """
    Indicate if there are more QueryAccumulators to iterate or not
    """
    cpdef bint has_next_accumulator(self)

    cpdef object transport(self)

