from dataclasses import dataclass

import numpy as np
from astropy import units as u
from astropy import constants as const

from mirage.calc import RayTracer
from mirage.util import PixelRegion
from mirage.model import TracingParameters, Starfield
from mirage.model import Starfield

@dataclass
class PointLensTracer(RayTracer):
  """
  Tracer for a point-lens mass model, where all the mass of a galaxy is modeled as a single point.
  """

  mass: u.Quantity

  def trace(self, rays: PixelRegion) -> u.Quantity:

    xs = rays.pixels.value

    deflection_factor = self.mass.to('solMass').value
    
    rs = xs[:, :, 0] * xs[:, :, 0] + xs[:, :, 1] * xs[:, :, 1]

    ys = np.copy(xs)

    ys[:, :, 0] -= deflection_factor * xs[:, :, 0] / rs
    ys[:, :, 1] -= deflection_factor * xs[:, :, 1] / rs

    return u.Quantity(ys, rays.unit)