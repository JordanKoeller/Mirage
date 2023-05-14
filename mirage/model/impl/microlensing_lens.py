from dataclasses import dataclass, field
from math import pi
import logging

import numpy as np
from astropy import units as u
from astropy import constants as const

from mirage.model import LensingSystem, TracingParameters
from mirage.util import PolarVec, Vec2D, DelegateRegistry

logger = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
@DelegateRegistry.register
class MicrolensingLens(LensingSystem):
    convergence: float
    shear: float
    starry_fraction: float

    def microtracing_parameters(self, position: Vec2D) -> TracingParameters:
        return TracingParameters(
            convergence=self.convergence,
            shear=self.shear,
            starry_fraction=self.starry_fraction,
        )

    @property
    def einstein_radius(self) -> u.Quantity:
        return 1 * self.xi_0
