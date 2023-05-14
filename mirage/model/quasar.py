from dataclasses import dataclass, field

from astropy.cosmology import Cosmology, WMAP7
from astropy import units as u


@dataclass(frozen=True)
class Quasar:
    """
    Defines a Quasar Source Object being lensed.
    """

    redshift: float
