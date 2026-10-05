# distutils: language = c++

cdef extern from "gravity_tree_tracer_ext.h":
  void trace_gravity_tree(
      double* rays_x, int num_rays,
      double kap, double gam,
      double* stars, int num_stars,
      double approximation_factor
      ) nogil
