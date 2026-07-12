from dataclasses import dataclass

from astropy import units as u


@dataclass
class Quasar:
  """
  Defines a Quasar Source Object being lensed.
  """

  redshift: float
  mass: u.Quantity
