from dataclasses import dataclass, field
from typing import Optional, Tuple
from functools import cache
from math import pi

import numpy as np
from astropy import units as u

from .initial_mass_function import Imf, ImfBrokenPowerlaw


@dataclass(frozen=True)
class Starfield:
    """
    Describes the parameters used to generate stars in a region.
    """

    initial_mass_function: ImfBrokenPowerlaw
    seed: int

    @cache
    def get_starfield(
        self, total_mass: u.Quantity, region_radius: u.Quantity
    ) -> Tuple[u.Quantity, u.Quantity]:
        num_stars = total_mass / 0.5
        masses = u.Quantity(
            self.initial_mass_function.generate_cluster(total_mass.to("solMass").value),
            "solMass",
        )
        masses = u.Quantity([0.5 for i in range(int(num_stars.value))], "solMass")
        num_stars = len(masses)

        positions: np.ndarray = np.ndarray(
            (num_stars, 2), dtype=np.float64
        )  # Buffer where each row is [mass, x, y]

        random_radii = region_radius * np.sqrt(
            self.initial_mass_function.random_number_generator.rand(num_stars)
        )

        # self._reset_rng(self.seed + 1)
        random_thetas = (
            2 * pi * self.initial_mass_function.random_number_generator.rand(num_stars)
        )

        positions[:, 0] = random_radii * np.cos(random_thetas)
        positions[:, 1] = random_radii * np.sin(random_thetas)

        return masses, u.Quantity(positions, region_radius.unit)

    def _reset_rng(self, seed: Optional[int] = None):
        self.initial_mass_function.set_seed(seed)
