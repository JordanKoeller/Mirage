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

cpdef np.ndarray[np.float64_t, ndim=1] slice_magmap(
    object magmap, # MagnificationMapReducer
    object start, #Vec2D
    object end, #Vec2D
)

cdef struct _Vec2D:
    double x
    double y

cdef struct _Int2D:
    int x
    int y

cdef _Vec2D _into_vec2d(object vec2D)

cdef _Int2D _sample_grid(_Vec2D tl, _Vec2D dxy, _Vec2D q)
