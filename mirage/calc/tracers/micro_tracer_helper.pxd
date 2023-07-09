# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as np

cpdef np.ndarray[np.float64_t, ndim=3] micro_ray_trace(
  np.ndarray[np.float64_t, ndim=3] rays,
  double kap,
  double gam,
  np.ndarray[np.float64_t, ndim=1] star_mass,
  np.ndarray[np.float64_t, ndim=2] star_pos,
  int thread_count)
