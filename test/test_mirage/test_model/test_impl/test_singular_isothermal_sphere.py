from unittest import TestCase

from astropy import units as u

from mirage.model.impl import SingularIsothermalSphereLens
from mirage.model import Quasar
from mirage.util import Vec2D, PolarVec


class TestPointLens(TestCase):

    def get_lens(self):
        return SingularIsothermalSphereLens(
            quasar=Quasar(1.2),
            redshift=0.7,
            velocity_dispersion=u.Quantity(300, "km/s"),
            star_fraction=0.8,
            shear=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.2, "rad")),
            ellipticity=PolarVec(u.Quantity(0.1, "rad"), u.Quantity(0.3, "rad")),
        )

    def testEinsteinRadius_success(self):
        lens = self.get_lens()
        er = lens.einstein_radius
        self.assertEqual(er.unit, u.arcsec)

    def testMicrotracingParameters_success(self):
        lens = self.get_lens()
        tracing_params = lens.microtracing_parameters(Vec2D(2, 3, "arcsec"))
