# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as np

cdef _Vec2D _into_vec2d(object vec2D):
  return _Vec2D(vec2D.x.value, _Vec2D(vec2D.y.value))

cdef _Int2D _sample_grid(_Vec2D tl, _Vec2D dxy, _Vec2D q):
  # Given the tl and resolution of a grid, return the indexed of q within the grid.
  # This uses nearest-neighbor sampling.
  return _Int2D(
    round((q.x-tl.x) / dxy.x),
    round((q.y-tl.y) / dxy.y)
  )

cpdef np.ndarray[np.float64_t, ndim=2] populate_magmap(
    np.ndarray[np.float64_t, ndim=3] query_locations,
    double query_radius,
    object tree):
  cdef int i, j, xx, yy, pos_count
  xx = query_locations.shape[0]
  yy = query_locations.shape[1]
  cdef np.ndarray[np.int64_t, ndim=2] buffer = np.zeros((xx, yy), dtype=np.int64)
  for i in range(xx):
    for j in range(yy):
      pos_count = tree.query_count(
        query_locations[i, j, 0], query_locations[i, j, 1], query_radius)
      buffer[i, j] += pos_count
  return buffer

cpdef np.ndarray[np.float64_t, ndim=1] populate_lightcurve(
    np.ndarray[np.float64_t, ndim=2] query_locations,
    double query_radius,
    object tree):
  cdef int i, num_queries, pos_count
  num_queries = query_locations.shape[0]
  cdef np.ndarray[np.int64_t, ndim=1] buffer = np.zeros(num_queries, dtype=np.int64)
  for i in range(num_queries):
    pos_count = tree.query_count(
      query_locations[i, 0], query_locations[i, 1], query_radius)
    buffer[i] = pos_count
  return buffer

cpdef np.ndarray[np.float64_t, ndim=2] slice_magmap(
    object magmap, # MagnificationMapReducer
    object start, #Vec2D
    object end, #Vec2D
):
  """
  Algorithm is as follows:

  1. Normalize to values in screen-space [0, resolution]
  2. Step along x-axis or y-axis by `m`, depending on if `m` <= 1 or `m` >= 1
    a. special-case vertical or horizontal lines.

  for x in range(x1, x2):
    y += m
    points.append(round(x), round(y))
  """
  cdef int x, y
  cdef np.ndarray[np.float64_t, ndim=2] canvas = magmap.magnitudes
  region = magmap.region
  cdef _Vec2D start = _into_vec2d(start.to(region.unit))
  cdef _Vec2D end = _into_vec2d(end.to(region.unit))
  tl_vec, br_vec = magmap.region.span
  tl = _into_vec2d(tl_vec)
  cdef _Vec2D dr = _into_vec2d(magmap.region.delta)



