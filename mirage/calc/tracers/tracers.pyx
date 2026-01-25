# distutils: language = c++

from mirage.calc.tracers cimport ctracers
cimport numpy as cnp

import numpy as np

cpdef cnp.ndarray[cnp.float64_t, ndim=3] trace_rays(
      cnp.ndarray[cnp.float64_t, ndim=3]rays,
      double kap,
      double gam,
      cnp.ndarray[cnp.float64_t, ndim=1] star_mass,
      cnp.ndarray[cnp.float64_t, ndim=2] star_pos
):
  width = rays.shape[0]
  height = rays.shape[1]
  cdef:
    cnp.float64_t[::1] rays_x = np.ascontiguousarray(rays[:,:,0]).flatten()
    cnp.float64_t[::1] rays_y = np.ascontiguousarray(rays[:,:,1]).flatten()
    cnp.float64_t[::1] stars_x = np.ascontiguousarray(star_pos[:, 0]).flatten()
    cnp.float64_t[::1] stars_y = np.ascontiguousarray(star_pos[:, 1]).flatten()
  ctracers.trace(
      &rays_x[0],  &rays_y[0],
      len(rays_x), kap, gam,
      &star_mass[0], &stars_x[0], &stars_y[0], len(stars_x))
  rays[:, :, 0] = np.reshape(rays_x, (width, height))
  rays[:, :, 1] = np.reshape(rays_y, (width, height))
  return rays

