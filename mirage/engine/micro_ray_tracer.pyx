# distutils: language=c++
# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

from libcpp.pair cimport pair

import numpy as np
cimport numpy as np

from cython.parallel import prange
cdef pair[double,double] ray_trace_helper(double &x, 
        double &y,
        double &gMax,
        double &gMin,
        double &kap,
        int &num_stars,
        double[:,:] stars) nogil:
    cdef int s
    cdef double dx, dy, retx, rety, r
    retx = gMin*x - kap*x
    rety = y*gMax - kap*y
    for s in range(num_stars):
        dx = x - stars[s,0]
        dy = y - stars[s,1]
        r = dx*dx + dy*dy
        retx -= stars[s,2]*dx/r
        rety -= stars[s,2]*dy/r
    return pair[double,double](retx,rety)

cpdef np.ndarray[np.float64_t,ndim=3] ray_trace(np.ndarray[np.float64_t, ndim=3] rays,
        double &kap,
        double &gam,
        int &thread_count,
        np.ndarray[np.float64_t, ndim=2] stars):
    cdef int i,j
    cdef int width = rays.shape[0]
    cdef int height = rays.shape[0]
    cdef int ns = stars.shape[0]
    cdef pair[double,double] traced_ray
    cdef double gMin = 1.0 - gam
    cdef double gMax = 1.0 + gam
    for i in prange(0,width,1,nogil=True,schedule='static',num_threads=thread_count):
        for j in range(0,height):
            traced_ray = ray_trace_helper(
                    rays[i,j,0], rays[i,j,1],
                    gMax, gMin,
                    kap,
                    ns, stars)
            rays[i,j,0] = traced_ray.first
            rays[i,j,1] = traced_ray.second
    return rays
