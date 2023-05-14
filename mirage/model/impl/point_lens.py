from dataclasses import dataclass, field
from math import pi
from typing import Optional

import numpy as np
from astropy import units as u
from astropy import constants as const

from mirage.model import LensingSystem, TracingParameters
from mirage.util import PolarVec, Vec2D, DelegateRegistry
from mirage.calc import RayTracer
from mirage.calc.tracers import PointLensTracer

@dataclass(kw_only=True, frozen=True)
@DelegateRegistry.register
class PointLens(LensingSystem):

  mass: u.Quantity

  @property
  def einstein_radius(self) -> u.Quantity:
    unitless_value = np.sqrt(
      4 * const.G * self.mass.to('kg') / self.effective_distance.to('m') / const.c / const.c)
    return u.Quantity(unitless_value.to('').value, 'rad').to('arcsec')

  def microtracing_parameters(self, position: Vec2D) -> TracingParameters:
    return TracingParameters(
      convergence=self._convergence(position), 
      shear=0, 
      starry_fraction=0)

  def get_ray_tracer(self) -> RayTracer:
    return PointLensTracer(mass=self.mass)

  def _convergence(self, position: Vec2D) -> float:
    einstein_radius = self.einstein_radius
    distance = position.magnitude.to(einstein_radius.unit)
    return (einstein_radius ** 2 / distance ** 2).to('').value