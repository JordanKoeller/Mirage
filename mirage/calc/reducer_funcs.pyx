# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

import numpy as np
cimport numpy as np

from libc.math cimport ceil, round, floor

cdef _Vec2D _into_vec2d(object vec2D):
  return _Vec2D(vec2D.x.value, vec2D.y.value)

cdef _Int2D _sample_grid(_Vec2D tl, _Vec2D dxy, _Vec2D q):
  # Given the tl and resolution of a grid, return the indexed of q within the grid.
  # This uses nearest-neighbor sampling.
  return _Int2D(
    int(round((q.x-tl.x) / dxy.x)),
    int(round((q.y-tl.y) / dxy.y))
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

cpdef np.ndarray[np.float64_t, ndim=1] slice_magmap(
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
  region = magmap.pixel_region
  start = start.to(region.unit)
  end = end.to(region.unit)
  reverse = False
  if end.x < start.x:
      reverse = True
      tmp = start
      start = end
      end = tmp
  tl_vec, br_vec = region.span
  cdef:
    double x, y
    np.ndarray[np.float64_t, ndim=2] canvas = magmap.magnitudes
    _Vec2D start_vec = _into_vec2d(((start - tl_vec).div(region.dims)).mul(region.resolution))
    _Vec2D end_vec = _into_vec2d(((end - tl_vec).div(region.dims)).mul(region.resolution))

  if floor(start_vec.x) == floor(end_vec.x):
    if start_vec.y < end_vec.y:
      return canvas[int(start_vec.y):int(end_vec.y), int(start_vec.x)]
    else:
      return canvas[int(end_vec.y):int(start_vec.y), int(start_vec.x)]
  if floor(start_vec.y) == floor(end_vec.y):
    # start_vec.x is always < end_vec.x so we don't need to flip.
    return canvas[int(start_vec.y), int(start_vec.x):int(end_vec.x)]

  cdef:
    double m = (end_vec.y - start_vec.y) / (end_vec.x - start_vec.x)
    int sz = 1
    int canvas_max_x = canvas.shape[0]
    int canvas_max_y = canvas.shape[1]
    np.ndarray[np.float64_t, ndim=1] ret = np.ndarray(int(region.resolution.x + region.resolution.y))
    double x1 = start_vec.x
    double y1 = start_vec.y
    double x2 = ceil(x1)
    double y2 = m * (x2 - x1) + y1
    int i, j
  ret[0] = canvas[
    max(min(<int>floor(y1), canvas_max_y), 0),
    min(max(<int>floor(x1), 0), canvas_max_x),
  ]
  x1 = x2
  y1 = y2
  x2 = min(x1 + 1.0, end_vec.x)
  y2 = m * (x2 - x1) + y1
  while x2 < end_vec.x:
      y = y1
      if m > 0:
        while y < y2:
          i = min(max(<int>floor(x1), 0), canvas_max_x)
          j = max(min(<int>floor(y), canvas_max_y), 0)
          ret[sz] = canvas[j, i]
          sz += 1
          y += 1.0
      else:
        while y > y2:
          i = min(max(<int>floor(x1), 0), canvas_max_x)
          j = max(min(<int>floor(y), canvas_max_y), 0)
          ret[sz] = canvas[j, i]
          sz += 1
          y -= 1.0
      x1 = x2
      y1 = y2
      x2 = min(x1 + 1.0, end_vec.x)
      y2 = m * (x2 - x1) + y1
  ret = ret[:sz]
  if reverse:
    ret = ret[::-1]
  return ret

