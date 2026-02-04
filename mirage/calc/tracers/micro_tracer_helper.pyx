# cython: profile=False, boundscheck=False, wraparound=False
# cython: cdivision=True
# cython: language_level=3

"""
SIMD Enablement:

    The current logic does not allow for SIMD because the memory-layout of rays is
    row-major order [x1,y1,x2,y2,x3,y3,...]. Since I don't have x-vals adjacent
    to other x-vals I can't effectively vectorize the input without shuffling to 
    allow for SIMD. For SIMD I need column-major order.

    Additionally, I have the outer for loop in a prange. I'm unsure if the compiler
    is smart enough to SIMD when a prange is involved.
"""

import numpy as np
cimport numpy as cnp

from libc.math cimport sqrt

from cython.parallel import prange
cimport cython


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef cnp.ndarray[cnp.float64_t, ndim=3] micro_ray_trace(
      cnp.float64_t[:, :, :] rays,
      double kap,
      double gam,
      cnp.float64_t[:] star_mass,
      cnp.float64_t[:, :] star_pos,
      int thread_count):
  cdef cnp.ndarray[cnp.float64_t, ndim=3] ret = np.copy(rays)
  cdef int i,j
  cdef int width = rays.shape[0]
  cdef int height = rays.shape[1]
  cdef int num_stars = star_mass.shape[0]
  cdef double gMin = 1.0 - gam
  cdef double gMax = 1.0 + gam
  cdef int s
  cdef double dx, dy, r
  for i in range(0, width):
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
