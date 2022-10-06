# distutils: language=c++
# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

from libcpp.pair cimport pair

import numpy as np
cimport numpy as np

cpdef np.ndarray[np.float64_t,ndim=3] ray_trace(
        np.ndarray[np.float64_t, ndim=3] rays,
        np.ndarray[np.float64_t, ndim=3] traced,
        double &kap,
        double &gam,
        int &thread_count,
        np.ndarray[np.float64_t, ndim=2] stars)

cpdef np.ndarray[np.float64_t,ndim=3] ray_trace_singlethreaded(
        np.ndarray[np.float64_t, ndim=3] rays,
        np.ndarray[np.float64_t, ndim=3] traced,
        double &kap,
        double &gam,
        np.ndarray[np.float64_t, ndim=2] stars)