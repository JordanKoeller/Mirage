from dataclasses import dataclass
import logging

import numpy as np
from astropy import units as u

from mirage.calc import RayTracer
from mirage.calc.tracers.micro_tracer_helper import trace
from mirage.model import Starfield
from mirage.util import PixelRegion

logger = logging.getLogger(__name__)


@dataclass
class MicrolensingRayTracer(RayTracer):
  starfield: Starfield
  star_mass: u.Quantity
  starfield_angular_radius: u.Quantity
  convergence: float
  shear: float

  def trace(self, rays: PixelRegion) -> u.Quantity:
    rays = rays.to("theta_0")

    stars_mass, stars_positions = self.starfield.get_starfield(
      self.star_mass, self.starfield_angular_radius
    )

    stars_positions = stars_positions.to("theta_0")

    pixels = rays.pixels.value

    logger.info(
      f"Running with {pixels.shape} (Total={pixels.shape[0] * pixels.shape[1]}) pixels"
    )

    traced_values = trace(
      pixels,
      self.convergence,
      self.shear,
      stars_mass.to("solMass").value,
      stars_positions.to("theta_0").value,
      True
    )

    return u.Quantity(traced_values, rays.unit)

  def __eq__(self, other: object) -> bool:
    if type(self) is not type(other):
      return False
    my_other: MicrolensingRayTracer = other  # type: ignore

    return (
      self.convergence == my_other.convergence
      and self.shear == my_other.shear
      and self.starfield == my_other.starfield
      and self.star_mass == my_other.star_mass
      and self.starfield_angular_radius == my_other.starfield_angular_radius
    )
