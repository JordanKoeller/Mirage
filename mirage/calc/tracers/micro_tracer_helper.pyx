# distutils: language = c++

from mirage.calc.tracers cimport micro_tracer_ext
cimport numpy as cnp

import numpy as np
import cython


cpdef cnp.ndarray[cnp.float64_t, ndim=3] trace(
      cnp.ndarray[cnp.float64_t, ndim=3] rays,
      double kap,
      double gam,
      cnp.ndarray[cnp.float64_t, ndim=1] star_mass,
      cnp.ndarray[cnp.float64_t, ndim=2] star_pos,
      int compute_parity,
      int allow_simd,
):
  width = rays.shape[0]
  height = rays.shape[1]
  if compute_parity:
      rays_mag = np.empty((rays.shape[0], rays.shape[1], 3), order='F', dtype=np.float64)
      rays_mag[:, :, 0] = rays[:, :, 0]
      rays_mag[:, :, 1] = rays[:, :, 1]
      rays = rays_mag
  elif not np.isfortran(rays):
      rays = np.asfortranarray(rays)
  if not np.isfortran(star_pos):
      star_pos = np.asfortranarray(star_pos)
  cdef:
      cnp.float64_t[::1, :, :] rays_view = rays
      cnp.float64_t[::1, :] star_pos_view = star_pos
      cnp.float64_t[::1] star_mass_view = star_mass
  if compute_parity:
      micro_tracer_ext.trace(
          &rays_view[0, 0, 0],  &rays_view[0, 0, 1],
          width * height, kap, gam,
          &star_mass_view[0], &star_pos_view[0, 0], &star_pos_view[0, 1], star_pos.shape[0],
          &rays_view[0, 0, 2], allow_simd)
  else:
      micro_tracer_ext.trace(
          &rays_view[0, 0, 0],  &rays_view[0, 0, 1],
          width * height, kap, gam,
          &star_mass_view[0], &star_pos_view[0, 0], &star_pos_view[0, 1], star_pos.shape[0],
          cython.NULL, allow_simd)
  return rays

cpdef bint supports_simd():
  return micro_tracer_ext.supports_simd()
