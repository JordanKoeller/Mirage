from unittest import TestCase

from astropy import units as u

from mirage.model.impl import PointLens
from mirage.model import Quasar
from mirage.util import Vec2D

class TestPointLens(TestCase):

  def get_lens(self):
    return PointLens(
      quasar=Quasar(redshift=1.2), 
      redshift=0.7,
      mass = u.Quantity(1e12, 'solMass')
    )

  def testEinsteinRadius_success(self):
    lens = self.get_lens()
    er = lens.einstein_radius
    self.assertEqual(er.unit, u.arcsec)

  def testMicrotracingParameters_success(self):
    lens = self.get_lens()
    tracing_params = lens.microtracing_parameters(Vec2D(2, 3, 'arcsec'))

  def testCriticalDensity_success(self):
    lens = self.get_lens()
    q = lens.critical_density

  def testEffectiveDistance_success(self):
    lens = self.get_lens()
    q = lens.effective_distance

  def testGetRayTracer_returnsRayTracer(self):
    lens = self.get_lens()
    tracer = lens.get_ray_tracer()