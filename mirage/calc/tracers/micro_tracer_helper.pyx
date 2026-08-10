# distutils: language = c++

from mirage.calc.tracers cimport micro_tracer_ext
cimport numpy as cnp

import numpy as np


cpdef cnp.ndarray[cnp.float64_t, ndim=3] trace(
      cnp.ndarray[cnp.float64_t, ndim=3] rays,
      double kap,
      double gam,
      cnp.ndarray[cnp.float64_t, ndim=1] star_mass,
      cnp.ndarray[cnp.float64_t, ndim=2] star_pos,
      int allow_simd
):
  width = rays.shape[0]
  height = rays.shape[1]
  if not np.isfortran(rays):
      rays = np.asfortranarray(rays)
  if not np.isfortran(star_pos):
      star_pos = np.asfortranarray(star_pos)
  cdef:
      cnp.float64_t[::1, :, :] rays_view = rays
      cnp.float64_t[::1, :] star_pos_view = star_pos
      cnp.float64_t[::1] star_mass_view = star_mass
  micro_tracer_ext.trace(
      &rays_view[0, 0, 0],  &rays_view[0, 0, 1],
      width * height, kap, gam,
      &star_mass_view[0], &star_pos_view[0, 0], &star_pos_view[0, 1], star_pos.shape[0],
      allow_simd)
  return rays

cpdef bint supports_simd():
  return micro_tracer_ext.supports_simd()
