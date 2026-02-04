# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as cnp

cpdef cnp.ndarray[cnp.float64_t, ndim=3] micro_ray_trace(
  cnp.float64_t[:, :, :] rays,
  double kap,
  double gam,
  cnp.float64_t[:] star_mass,
  cnp.float64_t[:, :] star_pos,
  int thread_count)
