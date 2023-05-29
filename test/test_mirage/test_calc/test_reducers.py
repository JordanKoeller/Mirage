from unittest import TestCase, skip

from matplotlib import pyplot as plt
from astropy import units as u
import numpy as np

from mirage.calc.reducers import LightCurvesReducer
from mirage.util import Region, Vec2D


class TestLightCurvesReducer(TestCase):

  def setUp(self):
    plt.cla()
    self.lcr = LightCurvesReducer(
        radius=1 * u.arcsec, resolution=10 / u.arcsec, num_curves=5, seed=12
    )
    self.region = Region(
        dims=Vec2D(10, 10, u.arcsec), center=Vec2D(1.2, -4.0, u.arcsec)
    )

  def testGetQuerySeeds_success(self):
    seeds = self.lcr.get_query_seeds(self.region)
    self.assertEqual(seeds.shape[0], self.lcr.num_curves)
    self.assertEqual(seeds.unit, u.arcsec)
    lows, highs = self.region.span
    for i in range(self.lcr.num_curves):
      x0, y0, x1, y1 = seeds[i].value
      self.assertAlmostWithin(x0, lows.x.value, highs.x.value)
      self.assertAlmostWithin(x1, lows.x.value, highs.x.value)
      self.assertAlmostWithin(y0, lows.y.value, highs.y.value)
      self.assertAlmostWithin(y1, lows.y.value, highs.y.value)

  def testGetQueryPoints_interpolatesWithSpecifiedResolution(self):
    lines = self.lcr.get_query_points(self.region)
    for line in lines:
      line = line.value
      dx = line[1, 0] - line[0, 0]
      dy = line[1, 1] - line[0, 1]
      r = np.sqrt(dx**2 + dy**2)
      self.assertAlmostEqual(r, 0.1)

  def assertAlmostWithin(self, v, low, high, tol=1e-8):
    self.assertGreaterEqual(v, low - tol)
    self.assertLessEqual(v, high + tol)
