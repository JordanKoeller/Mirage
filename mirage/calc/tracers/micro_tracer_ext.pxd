# distutils: language = c++

cdef extern from "micro_tracer_ext.h":
  void trace(
      double* rays_x, double* rays_y, int num_rays,
      double kap, double gam,
      double* stars_m, double* stars_x, double* stars_y, int num_stars,
      int allow_simd)

  bint supports_simd()
