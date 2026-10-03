# distutils: language = c++

cdef extern from "micro_tracer_ext.h":
  void trace(
      double* rays_x, double* rays_y, int num_rays,
      double kap, double gam,
      double* stars_m, double* stars_x, double* stars_y, int num_stars,
      double* mag, int allow_simd) nogil

  bint supports_simd()
