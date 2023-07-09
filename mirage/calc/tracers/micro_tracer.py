import multiprocessing
from dataclasses import dataclass
import logging

from astropy import units as u
import numpy as np

from mirage.calc import RayTracer
from mirage.calc.tracers.micro_tracer_helper import micro_ray_trace
from mirage.model import Starfield, TracingParameters
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
    core_count = multiprocessing.cpu_count()
    rays = rays.to("theta_0")

    stars_mass, stars_positions = self.starfield.get_starfield(
        self.star_mass, self.starfield_angular_radius
    )

    stars_positions = stars_positions.to("theta_0")

    pixels = rays.pixels.value

    logger.info(
        "Running with %d starts, M_tot=%.2f M_sun"
        % (stars_mass.shape[0], np.sum(stars_mass.value))
    )
    logger.info(
        f"Running with {pixels.shape} (Total={pixels.shape[0]*pixels.shape[1]}) pixels"
    )

    traced_values = micro_ray_trace(
        pixels,
        self.convergence,
        self.shear,
        stars_mass.to("solMass").value,
        stars_positions.to("theta_0").value,
        1,
    )

    return u.Quantity(traced_values, rays.unit)
