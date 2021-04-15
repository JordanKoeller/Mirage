# cython: boundscheck=False, wraparound=False, embedsignature=True, cdivision=True, cdivision_warnings=True
from cython.view cimport array as cvarray
cimport numpy as np
import numpy as np

cdef void trace_single(FLOAT &kap,
                            FLOAT &gMax,
                            FLOAT &gMin,
                            FLOAT[:, ::1] stars,
                            INT &star_count,
                            FLOAT * ray) nogil:
  cdef:
    INT s
    FLOAT dx, dy, retx, rety, r
  retx = gMin*ray[0] - kap*ray[0]
  rety = gMax*ray[1] - kap*ray[1]
  for s in range(star_count):
    dx = ray[0] - stars[s,0]
    dy = ray[1] - stars[s,1]
    r = dx*dx + dy*dy
    retx -= stars[s,2]*dx/r
    rety -= stars[s,2]*dy/r
  ray[0] = retx
  ray[1] = rety
  
cpdef np.ndarray[FLOAT, ndim=2] trace_bundle(FLOAT kap,
                                 FLOAT gMax,
                                 FLOAT gMin,
                                 FLOAT[:, ::1] stars,
                                 INT star_count,
                                 FLOAT x0,
                                 FLOAT y0,
                                 FLOAT dx,
                                 FLOAT dy,
                                 np.ndarray[LONG, ndim=1] input_rays,
                                 LONG chunk_sz,
                                 INT x_length,
                                 INT y_length):
  cdef np.ndarray[FLOAT, ndim=2] rays = np.ndarray((chunk_sz, 2), dtype=np.float64)
  cdef LONG i = 0
  cdef LONG j = 0
  cdef LONG rI = 0
  cdef INT s = 0
  cdef FLOAT s_dx, s_dy, r, retx, rety
  with nogil:
    for rI in range(0, chunk_sz):
        i = input_rays[rI] % x_length
        j = input_rays[rI] // x_length
        rays[rI, 0] = x0 + dx*(<FLOAT> i)
        rays[rI, 1] = y0 + dy*(<FLOAT> j)
        retx = gMin*rays[rI, 0] - kap*rays[rI, 0]
        rety = gMax*rays[rI, 1] - kap*rays[rI, 1]
        for s in range(star_count):
          s_dx = rays[rI, 0] - stars[s, 0]
          s_dy = rays[rI, 1] - stars[s, 1]
          r = s_dx*s_dx+s_dy*s_dy
          retx -= stars[s, 2]*s_dx / r
          retx -= stars[s, 2]*s_dy / r
        rays[rI, 0] = retx
        rays[rI, 1] = rety
  print(rays)
  return rays