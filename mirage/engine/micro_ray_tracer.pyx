# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

import numpy as np
cimport numpy as np

from cython.parallel import prange
cpdef np.ndarray[np.float64_t,ndim=3] ray_trace_singlethreaded(
        np.ndarray[np.float64_t, ndim=3] rays,
        np.ndarray[np.float64_t, ndim=3] traced,
        double &kap,
        double &gam,
        np.ndarray[np.float64_t, ndim=2] stars):
    cdef int i,j
    cdef int width = rays.shape[0]
    cdef int height = rays.shape[1]
    cdef int num_stars = stars.shape[0]
    cdef double gMin = 1.0 - gam
    cdef double gMax = 1.0 + gam
    cdef int s
    cdef double dx, dy, r
    with nogil:
        for i in range(0,width):
            for j in range(0,height):
                traced[i,j,0] = gMin*rays[i,j,0] - kap*rays[i,j,0]
                traced[i,j,1] = rays[i,j,1]*gMax - kap*rays[i,j,1]
                for s in range(num_stars):
                    dx = rays[i,j,0] - stars[s,0]
                    dy = rays[i,j,1] - stars[s,1]
                    r = dx*dx + dy*dy
                    traced[i,j,0] -= stars[s,2]*dx/r
                    traced[i,j,1] -= stars[s,2]*dy/r
    return traced

cpdef np.ndarray[np.float64_t,ndim=3] ray_trace(
        np.ndarray[np.float64_t, ndim=3] rays,
        np.ndarray[np.float64_t, ndim=3] traced,
        double &kap,
        double &gam,
        int &thread_count,
        np.ndarray[np.float64_t, ndim=2] stars):
    cdef int i,j
    cdef int width = rays.shape[0]
    cdef int height = rays.shape[1]
    cdef int num_stars = stars.shape[0]
    cdef double gMin = 1.0 - gam
    cdef double gMax = 1.0 + gam
    cdef int s
    cdef double dx, dy, r
    for i in prange(0,width,1,nogil=True,schedule='static',num_threads=thread_count):
        for j in range(0,height):
            traced[i,j,0] = gMin*rays[i,j,0] - kap*rays[i,j,0]
            traced[i,j,1] = rays[i,j,1]*gMax - kap*rays[i,j,1]
            for s in range(num_stars):
                dx = rays[i,j,0] - stars[s,0]
                dy = rays[i,j,1] - stars[s,1]
                r = dx*dx + dy*dy
                traced[i,j,0] -= stars[s,2]*dx/r
                traced[i,j,1] -= stars[s,2]*dy/r
    return traced
