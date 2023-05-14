from unittest import TestCase

from astropy.cosmology import WMAP9
from astropy import units as u
import numpy as np

from mirage.calc.tracers import PointLensTracer
from mirage.util import PixelRegion, Vec2D
from mirage.model import Quasar
from mirage.model.impl import PointLens
from mirage.calc.tracers.micro_tracer_helper import micro_ray_trace

class TestPointLensTracer(TestCase):

  def setUp(self):
    self.tracer = PointLensTracer(
      u.Quantity(1e12, 'solMass'))

  def testTrace_success(self):
    region = PixelRegion(
      dims=Vec2D(25, 25, 'arcsec'),
      center=Vec2D.zero_vector('arcsec'),
      resolution=Vec2D.unitless(500, 500))
    output = self.tracer.trace(region)
    self.assertEqual(output.unit, u.arcsec)

class TestMicroTracer(TestCase):

  def testTrace_oneLargeStar_sameResultAsPointLenseTracer(self):
    point_lens = PointLens(quasar=Quasar(2.0), redshift=0.5, mass=u.Quantity(1e12, 'solMass'))
    region = PixelRegion(
      dims=Vec2D(5, 55, 'arcsec'),
      center=Vec2D.zero_vector('arcsec'),
      resolution=Vec2D.unitless(500, 500))
    tracer = point_lens.get_ray_tracer()
    sample_ray = region.pixels
    micro_traced = micro_ray_trace(sample_ray, 0.0, 0.0, np.array([1e12]), np.array([[0.0, 0.0]]), 1)
    macro_traced = tracer.trace(region)
    self.assertAlmostEqual(micro_traced.value.tolist(), macro_traced.value.tolist())