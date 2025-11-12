from unittest import TestCase

from astropy import units as u
import numpy as np

from mirage.model import Starfield
from mirage.model.initial_mass_function import Kroupa2001


class TestStarfield(TestCase):
    def testGetStarfield_success(self):
        starfield = Starfield(initial_mass_function=Kroupa2001(), seed=123)

        mass, _p = starfield.get_starfield(
            100.0 * u.M_sun, u.Quantity(100.0, "uas")
        )

        total = np.sum(mass)
        self.assertAlmostEqual(total.value, 100.0, delta=3.0)

    def testGetStarfield_smallFieldsAreSubsetsOfLargeFields(self):
        starfield = Starfield(initial_mass_function=Kroupa2001(), seed=123)

        small_field, small_pos = starfield.get_starfield(
            10.0 * u.M_sun, u.Quantity(100.0, "uas")
        )
        large_field, large_pos = starfield.get_starfield(
            100.0 * u.M_sun, u.Quantity(100.0, "uas")
        )

        self.assertEqual(small_field.shape[0], small_pos.shape[0])
        self.assertEqual(large_field.shape[0], large_pos.shape[0])

        for sm, lg in zip(small_field.value.tolist(), large_field.value.tolist()[:len(small_field)]):
            self.assertAlmostEqual(sm, lg)

        for sm, lg in zip(small_pos.value[:,0].tolist(), large_pos.value[:,0].tolist()[:len(small_pos)]):
            self.assertAlmostEqual(sm, lg)

        for sm, lg in zip(small_pos.value[:,1].tolist(), large_pos.value[:,1].tolist()[:len(small_pos)]):
            self.assertAlmostEqual(sm, lg)

