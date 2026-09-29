from dataclasses import dataclass

import numpy as np
from astropy import units as u

from mirage.calc import RayTracer
from mirage.util import PixelRegion


@dataclass
class PointLensTracer(RayTracer):
  """
  Tracer for a point-lens mass model, where all the mass of a galaxy is modeled as a single point.
  """

  mass: u.Quantity
  einstein_radius: u.Quantity

  def trace(self, rays: PixelRegion) -> u.Quantity:
    xs = rays.pixels.value
    xs_norm = rays.pixels.to(self.einstein_radius)

    deflection_factor = self.mass.to("solMass").value

    rs = xs[:, :, 0] * xs[:, :, 0] + xs[:, :, 1] * xs[:, :, 1]
    rs_norm = xs_norm[:, :, 0] * xs_norm[:, :, 0] + xs_norm[:, :, 1] * xs_norm[:, :, 1]

    ys = np.ndarray((xs.shape[0], xs.shape[1], 3), dtype=np.float64)
    ys[:, :, 0] = xs[:, :, 0]
    ys[:, :, 1] = xs[:, :, 1]
    ys[:, :, 2] = 1 / (1- ((rs_norm / self.einstein_radius**2).to("").value)**2)
    ys[:, :, 0] -= deflection_factor * xs[:, :, 0] / rs
    ys[:, :, 1] -= deflection_factor * xs[:, :, 1] / rs

    return u.Quantity(ys, rays.unit)
