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

cdef clip(int v, int mn, int mx):
  return max(min(v, mx), mn)

cdef lerp(double a, double b, double x):
    return b * x + a * (1 - x) 


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

  if floor(start_vec.x) == floor(end_vec.x): # Vertical line
    if start_vec.y < end_vec.y:
      return canvas[int(start_vec.y):int(end_vec.y) + 1, int(start_vec.x)]
    else:
      return canvas[int(end_vec.y):int(start_vec.y) + 1, int(start_vec.x)]
  if floor(start_vec.y) == floor(end_vec.y): # horizontal line
    # start_vec.x is always < end_vec.x so we don't need to flip.
    return canvas[int(start_vec.y), int(start_vec.x):int(end_vec.x) + 1]

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
    int i = min(max(<int>floor(x1), 0), canvas_max_x)
    int j = max(min(<int>floor(y1), canvas_max_y), 0)
  ret[0] = canvas[j, i]
  x1 = x2
  y1 = y2
  x2 = min(x1 + 1.0, end_vec.x)
  y2 = m * (x2 - x1) + y1
  while x1 < end_vec.x:
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

cpdef np.ndarray[np.int64_t, ndim=1] merge_index_lists(
    np.ndarray[np.int64_t, ndim=1] a,
    np.ndarray[np.int64_t, ndim=1] b
):
  np.sort(a)
  np.sort(b)
  cdef:
    int a_i = 0
    int b_i = 0
    int r_i = 0
    np.ndarray[np.int64_t, ndim=1] ret = np.ndarray(len(a) + len(b), dtype=np.int64)
  while a_i < len(a) or b_i < len(b):
    if a_i == len(a):
      ret[r_i] = b[b_i]
      r_i += 1
      b_i += 1
      continue
    if b_i == len(b):
      ret[r_i] = a[a_i]
      r_i += 1
      a_i += 1
      continue
    if a[a_i] < b[b_i]:
      ret[r_i] = a[a_i]
      a_i += 1
      r_i += 1
    elif b[b_i] < a[a_i]:
      ret[r_i] = b[b_i]
      b_i += 1
      r_i += 1
    elif a[a_i] == b[b_i]:
      ret[r_i] = b[b_i]
      b_i += 1
      a_i += 1
      r_i += 1
  return ret[:r_i]

cpdef np.ndarray[np.int32_t, ndim=2] populate_lensed_image(
    np.ndarray[np.int64_t, ndim=1] source_indices,
    object lens_region, # Pixel Region
    object canvas_resolution # Vec2D
):
  cdef:
    int canvas_width = int(canvas_resolution.x)
    int canvas_height = int(canvas_resolution.y)
    np.ndarray[np.int32_t, ndim=2] canvas = np.zeros((canvas_width, canvas_height), dtype=np.int32)
    double canvas_x = float(canvas_resolution.x)
    double canvas_y = float(canvas_resolution.y)
    int i, n = source_indices.shape[0]
    double x, y
    int xx, yy
    int source_width = int(lens_region.resolution.x)
    int source_height = int(lens_region.resolution.y)
    double source_width_d = float(lens_region.resolution.x)
    double source_height_d = float(lens_region.resolution.y)
  for i in range(n):
    if source_indices[i] == -1:
      break
    x = float(source_indices[i] // source_height)
    y = float(source_indices[i] % source_height)
    xx = clip(int(round(x / source_width_d * (canvas_width))), 0, int(canvas_width -1))
    yy = clip(int(round(y / source_height_d * (canvas_height))), 0, int(canvas_height -1))
    canvas[xx, yy] += 1
  return canvas


cpdef void draw_lensed_image(
    np.ndarray[np.uint8_t, ndim=3] canvas,
    np.ndarray[np.int32_t, ndim=2] brightness,
    object colormap,
    double normalization_factor,
):
    # Reset back to baseline
    canvas[:, :] = colormap["BACKGROUND"]
    cdef:
        int i, j, n = canvas.shape[0], m = canvas.shape[1]
        double a, b, x
        np.ndarray[np.float64_t, ndim=1] pos_start = colormap["POS_PARITY_START"]
        np.ndarray[np.float64_t, ndim=1] pos_stop = colormap["POS_PARITY_STOP"]
        np.ndarray[np.float64_t, ndim=1] neg_start = colormap["NEG_PARITY_START"]
        np.ndarray[np.float64_t, ndim=1] neg_stop = colormap["NEG_PARITY_STOP"]
    for i in range(n):
        for j in range(m):
            x = float(brightness[i, j])
            if x > 0.0:
                canvas[i, j, 0] = int(lerp(pos_start[0], pos_stop[0], x / normalization_factor))
                canvas[i, j, 1] = int(lerp(pos_start[1], pos_stop[1], x / normalization_factor))
                canvas[i, j, 2] = int(lerp(pos_start[2], pos_stop[2], x / normalization_factor))
            if brightness[i, j] < 0.0:
                canvas[i, j, 0] = int(lerp(neg_start[0], neg_stop[0], -x / normalization_factor))
                canvas[i, j, 1] = int(lerp(neg_start[1], neg_stop[1], -x / normalization_factor))
                canvas[i, j, 2] = int(lerp(neg_start[2], neg_stop[2], -x / normalization_factor))




