# distutils: language=c++
# cython: profile=True, boundscheck=False, wraparound=False,embedsignature=True

from libc.math cimport sin, cos, atan2, sqrt ,atan, atanh, pi
from libcpp.pair cimport pair
from libcpp.vector cimport vector
from numpy cimport int32_t, float64_t, ndarray

import cython
from cython.parallel import prange

cdef pair[double,double] ray_trace_helper(double &x,
    double &y,
    double &dL,
    double &dLS,
    double &dS,
    double &shear_mag,
    double &shear_angle,
    double &el_mag,
    double &el_angle,
    double &b) nogil:
    cdef double r, cosShear, sinShear, cosEl, sinEl, q1, res_x, res_y
    cdef double eex, eey, phi, ex, ey
    r = sqrt(x*x + y*y)
    cosShear = cos(-shear_angle)
    sinShear = sin(-shear_angle)
    cosEl = cos(el_angle)
    sinEl = sin(el_angle)
    q1 = sqrt(1.0 - el_mag*el_mag)
    #Elliptical SIS
    if r != 0.0:
        if el_mag == 1.0:
            res_x = x*b/r
            res_y = y*b/r
        else:
            eex = x*sinEl+y*cosEl
            eey = y*sinEl-x*cosEl
            ex = el_mag*b*atan(q1*eex/sqrt(el_mag*el_mag*eex*eex+eey*eey))/q1
            ey = el_mag*b*atanh(q1*eey/sqrt(el_mag*el_mag*eex*eex+eey*eey))/q1
            res_x = ex*sinEl-ey*cosEl
            res_y = ex*sinEl + ey*sinEl

    #shear
    phi = 2.0 * (pi/2.0 - shear_angle) - atan2(y,x)
    res_x += shear_mag*r*cos(phi)
    res_y += shear_mag*r*sin(phi)
    res_x = x - res_x
    res_y = y - res_y
    return pair[double,double](res_x,res_y)


cpdef ray_trace(np.ndarray[np.float64_t, ndim=3] rays,
    double dL,
    double dS,
    double dLS,
    double shear_mag,
    double shear_angle,
    double el_mag,
    double el_angle,
    double b,
    int thread_count):
    cdef int i,j
    cdef int width = rays.shape[0]
    cdef int height = rays.shape[1]
    cdef pair[double,double] traced_ray
    for i in prange(0, width,1,nogil=True,schedule='static',num_threads=thread_count):
        for j in range(0,height):
            traced_ray = ray_trace_helper(
                rays[i,j,0],rays[i,j,1],
                dL,dLS,dS,
                shear_mag,shear_angle,
                el_mag,el_angle,
                b)
            rays[i,j,0] = traced_ray.first
            rays[i,j,1] = traced_ray.second
    return rays
