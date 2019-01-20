# distutils: language=c++
# cython: profile=False, boundscheck=False, wraparound=False,embedsignature=False
# cython: language_level=3

from libc.math cimport sin, cos, atan2, sqrt ,atan, atanh, pi
from libcpp.pair cimport pair

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
    cosEl = cos(el_angle)
    sinEl = sin(el_angle)
    sinShear = shear_mag*sin(2*shear_angle)
    cosShear = shear_mag*cos(2*shear_angle)
    q1 = sqrt(1.0 - el_mag*el_mag)
    #Elliptical SIS
    if r != 0.0:
        if el_mag == 1.0:
            res_x = x*b/r
            res_y = y*b/r
        else:
            eex = x*sinEl+y*cosEl
            eey = y*sinEl-x*cosEl
            ex = b*atan(q1*eex/sqrt(el_mag*el_mag*eex*eex+eey*eey))/q1
            ey = b*atanh(q1*eey/sqrt(el_mag*el_mag*eex*eex+eey*eey))/q1
            res_x = ex*sinEl-ey*cosEl
            res_y = ex*sinEl + ey*sinEl
    else:
        res_x = 0.0
        res_y = 0.0

    #shear
    # phi = 2.0 * (pi/2.0 - shear_angle) - atan2(y,x)
    res_x += cosShear*x+sinShear*y
    res_y += sinShear*x - cosShear*y
    res_x = x - res_x
    res_y = y - res_y
    return pair[double,double](res_x,res_y)




cdef pair[double,double] micro_ray_helper(double &conv,
                                          double &sMin,
                                          double &sMax,
                                          double &x,
                                          double &y) nogil:
    cdef double ret_x = sMin*x - conv*x
    cdef double ret_y = sMax*y - conv*y
    return pair[double,double](ret_x,ret_y)

cpdef int raw_brightness(object parameters):
    center = parameters.ray_region.center
    cdef:
        double conv = parameters.convergence(center)
        double shear = parameters.shear(center)
        double dx = parameters.ray_region.dTheta.x.to(parameters.xi_0).value
        double dy = parameters.ray_region.dTheta.y.to(parameters.xi_0).value
        double radius = parameters.quasar.radius.to(parameters.eta_0).value
        double gMax = 1.0 + shear
        double gMin = 1.0 - shear
        pair[double,double] ray
        double qx, qy
        int flag = 1, i, j, counter = 1
        int level = 1
    with nogil:
        while flag == 1:
            flag = 0
            qx = -dx*level
            for i in range(-level,level):
                qy = i*dy
                ray = micro_ray_helper(conv,gMin,gMax,qx,qy)
                if ray.first*ray.first+ray.second*ray.second < radius:
                    flag = 1
                    counter += 1
            qx = dx*level
            for i in range(-level,level):
                qy = i*dy
                ray = micro_ray_helper(conv,gMin,gMax,qx,qy)
                if ray.first*ray.first+ray.second*ray.second < radius:
                    flag = 1
                    counter += 1
            qy = -dy*level
            for i in range(-level+1,level-1):
                qx = i*dx
                ray = micro_ray_helper(conv,gMin,gMax,qx,qy)
                if ray.first*ray.first+ray.second*ray.second < radius:
                    flag = 1
                    counter += 1
            qy = dy*level
            for i in range(-level+1,level-1):
                qx = i*dx
                ray = micro_ray_helper(conv,gMin,gMax,qx,qy)
                if ray.first*ray.first+ray.second*ray.second < radius:
                    flag = 1
                    counter += 1
            level += 1
    print("Raw value of %d" % counter)
    return counter




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
    print("Tracing here")
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
