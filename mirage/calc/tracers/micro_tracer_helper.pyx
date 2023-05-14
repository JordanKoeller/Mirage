# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

import numpy as np
cimport numpy as np

from libc.math cimport sqrt

from cython.parallel import prange

cpdef np.ndarray[np.float64_t, ndim=3] micro_ray_trace(
    np.ndarray[np.float64_t, ndim=3] rays,
    double kap,
    double gam,
    np.ndarray[np.float64_t, ndim=1] star_mass,
    np.ndarray[np.float64_t, ndim=2] star_pos,
    int thread_count):
  cdef np.ndarray[np.float64_t, ndim=3] ret = np.copy(rays)
  cdef int i,j
  cdef int width = rays.shape[0]
  cdef int height = rays.shape[1]
  cdef int num_stars = star_mass.shape[0]
  cdef double gMin = 1.0 - gam
  cdef double gMax = 1.0 + gam
  cdef int s
  cdef double dx, dy, r
  for i in prange(0, width, 1, nogil=True, schedule='static', num_threads=thread_count):
    for j in range(0,height):
      ret[i,j,0] = gMin*rays[i,j,0] - kap*rays[i,j,0]
      ret[i,j,1] = rays[i,j,1]*gMax - kap*rays[i,j,1]
      for s in range(num_stars):
        dx = rays[i,j,0] - star_pos[s,0]
        dy = rays[i,j,1] - star_pos[s,1]
        r = dx*dx + dy*dy
        ret[i,j,0] -= star_mass[s]*dx/r
        ret[i,j,1] -= star_mass[s]*dy/r
  return ret
