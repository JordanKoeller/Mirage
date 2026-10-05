# distutils: language=c++
# cython: profile=True, boundscheck=False, wraparound=False, embedsignature=True

from mirage.calc.tracers cimport bruteforce_tracer_ext
from mirage.calc.tracers cimport gravity_tree_tracer_ext
cimport numpy as cnp

import numpy as np
import cython


cpdef cnp.ndarray[cnp.float64_t, ndim=3] trace_bruteforce(
      cnp.ndarray[cnp.float64_t, ndim=3] rays,
      double kap,
      double gam,
      cnp.ndarray[cnp.float64_t, ndim=1] star_mass,
      cnp.ndarray[cnp.float64_t, ndim=2] star_pos,
      int compute_parity,
      int allow_simd,
):
  cdef int width = rays.shape[0]
  cdef int height = rays.shape[1]
  cdef double* nullptr = cython.NULL
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
  with nogil:
      if compute_parity:
          bruteforce_tracer_ext.trace_bruteforce(
              &rays_view[0, 0, 0],  &rays_view[0, 0, 1],
              width * height, kap, gam,
              &star_mass_view[0], &star_pos_view[0, 0], &star_pos_view[0, 1], star_pos.shape[0],
              &rays_view[0, 0, 2], allow_simd)
      else:
          bruteforce_tracer_ext.trace_bruteforce(
              &rays_view[0, 0, 0],  &rays_view[0, 0, 1],
              width * height, kap, gam,
              &star_mass_view[0], &star_pos_view[0, 0], &star_pos_view[0, 1], star_pos.shape[0],
              nullptr, allow_simd)
  return rays

cpdef cnp.ndarray[cnp.float64_t, ndim=3] trace_gravity_tree(
      cnp.ndarray[cnp.float64_t, ndim=3] rays,
      double kap,
      double gam,
      cnp.ndarray[cnp.float64_t, ndim=1] star_mass,
      cnp.ndarray[cnp.float64_t, ndim=2] star_pos,
      double approximation_factor,
):
  cdef int width = rays.shape[0]
  cdef int height = rays.shape[1]
  cdef int num_stars = star_mass.shape[0]
  if not np.isfortran(rays):
      rays = np.asfortranarray(rays)
  stars = np.empty((star_pos.shape[0], 3), order='F', dtype=np.float64)
  stars[:, 0:2] = star_pos
  stars[:, 2] = star_mass
  cdef:
      cnp.float64_t[::1, :, :] rays_view = rays
      cnp.float64_t[::1, :] stars_view = stars
  with nogil:
      gravity_tree_tracer_ext.trace_gravity_tree(
          &rays_view[0, 0, 0], width * height,
          kap, gam,
          &stars_view[0, 0], num_stars, approximation_factor)
  return rays

cpdef bint supports_simd():
  return True
