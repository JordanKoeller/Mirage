# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

from libcpp.pair cimport pair

import numpy as np
cimport numpy as np
cimport cython

ctypedef np.float64_t FLOAT
ctypedef np.int32_t INT
ctypedef np.int16_t SHORT
ctypedef np.int64_t LONG

@cython.boundscheck(False)
@cython.wraparound(False)
cdef void trace_single(FLOAT &kap,
                            FLOAT &gMax,
                            FLOAT &gMin,
                            FLOAT[:, ::1] stars,
                            INT &start_count,
                            FLOAT * ray) nogil


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef np.ndarray[FLOAT, ndim=2] trace_bundle(FLOAT kap,
                                 FLOAT gMax,
                                 FLOAT gMin,
                                 FLOAT[:, ::1] stars,
                                 INT star_count,
                                 FLOAT x0,
                                 FLOAT y0,
                                 FLOAT dx,
                                 FLOAT dy,
                                 np.ndarray[LONG, ndim=1] input_rays,
                                 LONG chunk_sz,
                                 INT x_length,
                                 INT y_length)
  

# @cython.boundscheck(False)
# @cython.wraparound(False)
# cpdef FLOAT[::1] seed_rays(FLOAT dx,
#                            FLOAT dy,
#                            FLOAT x0,
#                            FLOAT y0,
#                            int num_x,
#                            int num_y,
#                            FLOAT[::1] ray)