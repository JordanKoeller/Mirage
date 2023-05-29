# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as np

cpdef np.ndarray[np.float64_t, ndim=2] populate_magmap(
  np.ndarray[np.float64_t, ndim=3] query_locations,
  double query_radius,
  object tree)

cpdef np.ndarray[np.float64_t, ndim=1] populate_lightcurve(
  np.ndarray[np.float64_t, ndim=2] query_locations,
  double query_radius,
  object tree)
