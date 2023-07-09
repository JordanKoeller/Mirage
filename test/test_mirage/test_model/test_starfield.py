from unittest import TestCase

from astropy import units as u
import numpy as np

from mirage.model import Starfield
from mirage.model.initial_mass_function import Kroupa2001


class TestStarfield(TestCase):

  def testGetStarfield_success(self):
    starfield = Starfield(initial_mass_function=Kroupa2001(), seed=123)

    mass, _p = starfield.get_starfield(100.0 * u.M_sun, u.Quantity(100.0, "uas"))

    total = np.sum(mass)
    self.assertAlmostEqual(total.value, 100.0, delta=3.0)

  def testGetStarfield_smallFieldsAreSubsetsOfLargeFields(self):
    starfield = Starfield(initial_mass_function=Kroupa2001(), seed=123)

    smallField, _p = starfield.get_starfield(10.0 * u.M_sun, u.Quantity(100.0, "uas"))
    largeField, _p = starfield.get_starfield(100.0 * u.M_sun, u.Quantity(100.0, "uas"))

    self.assertListEqual(
        smallField.value.tolist(), largeField.value[: len(smallField)].tolist()
    )

  def testGetStarfield_distributesStarsInADisk(self):
    starfield = Starfield(initial_mass_function=Kroupa2001(), seed=123)

    _m, small_pos = starfield.get_starfield(10.0 * u.M_sun, u.Quantity(100.0, "uas"))
    _m, large_pos = starfield.get_starfield(100.0 * u.M_sun, u.Quantity(100.0, "uas"))
