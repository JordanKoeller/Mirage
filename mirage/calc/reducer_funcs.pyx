# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as np

cpdef np.ndarray[np.float64_t, ndim=2] populate_magmap(
    np.ndarray[np.float64_t, ndim=3] query_locations,
    double query_radius,
    object tree):
  cdef int i, j, xx, yy
  xx = query_locations.shape[0]
  yy = query_locations.shape[1]
  cdef np.ndarray[np.int64_t, ndim=2] buffer = np.zeros((xx, yy), dtype=np.int64)
  for i in range(xx):
    for j in range(yy):
      pos_count = tree.query_count(
        query_locations[i, j, 0], query_locations[i, j, 1], query_radius)
      buffer[i, j] += pos_count
  return buffer
