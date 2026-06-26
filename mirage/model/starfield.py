from dataclasses import dataclass
from typing import Optional, Tuple
from functools import cache
from math import pi
import logging

import numpy as np
from astropy import units as u

from .initial_mass_function import ImfBrokenPowerlaw

logger = logging.getLogger(__name__)


@dataclass
class Starfield:
    """
    Describes the parameters used to generate stars in a region.
    """

    initial_mass_function: ImfBrokenPowerlaw
    seed: int

    def get_starfield(
        self, total_mass: u.Quantity, region_radius: u.Quantity
    ) -> tuple[u.Quantity, u.Quantity]:
        """
        Generate and return description of the specified starfield.

        Returns:
          (masses, positions)
        """
        return _get_starfield(self.initial_mass_function, self.seed, total_mass, region_radius)

def _reset_rng(self, seed: Optional[int] = None):
    self.initial_mass_function.set_seed(seed)

@cache
def _get_starfield(
    initial_mass_function: ImfBrokenPowerlaw, seed: int,
    total_mass: u.Quantity, region_radius: u.Quantity,
) -> tuple[u.Quantity, u.Quantity]:
    """
    Helper function in calling get_starfield.

    This allows us to pass members of `Starfield` into the function so that the @cache
    decorator can listen for them changing.
    """
    initial_mass_function.set_seed(seed)

    num_stars = total_mass / 0.5
    masses = u.Quantity(
        initial_mass_function.generate_cluster(
            total_mass.to("solMass").value
        ),
        "solMass",
    )
    num_stars = len(masses)

    positions: np.ndarray = np.ndarray(
        (num_stars, 2), dtype=np.float64, order='F'
    )  # Buffer where each row is [x, y]

    initial_mass_function.set_seed(seed + 1)
    random_radii = region_radius * np.sqrt(
        initial_mass_function.random_number_generator.rand(num_stars)
    )

    initial_mass_function.set_seed(seed + 2)
    random_thetas = (
        2
        * pi
        * initial_mass_function.random_number_generator.rand(num_stars)
    )

    positions[:, 0] = random_radii * np.cos(random_thetas)
    positions[:, 1] = random_radii * np.sin(random_thetas)

    logger.info(f"Generated {num_stars} ({masses.sum()})")

    return masses, u.Quantity(positions, region_radius.unit)

