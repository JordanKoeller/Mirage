from unittest import TestCase

from astropy import units as u
import numpy as np

from mirage.util import Region, PixelRegion, Vec2D


class TestPixelRegion(TestCase):

  def testDelta_success(self):
    region = PixelRegion(dims=Vec2D(5, 5, "m"), resolution=Vec2D.unitless(4, 5))
    delta = region.delta

    expected = Vec2D(5 / 4, 5 / 5, "m")

    self.assertAlmostEqual(expected.x.value, delta.x.value)
    self.assertAlmostEqual(expected.y.value, delta.y.value)
    self.assertEqual(expected.unit, delta.unit)

  def testPixels_givesCoordinatesForCenterOfEachPixelOnGrid(self):
    region = PixelRegion(
        dims=Vec2D(3, 3, "m"),
        center=Vec2D(2, 2, "m"),
        resolution=Vec2D.unitless(3, 3),
    )

    actual = region.pixels

    expected = [
        [[1, 1], [2, 1], [3, 1]],
        [[1, 2], [2, 2], [3, 2]],
        [[1, 3], [2, 3], [3, 3]],
    ]

    self.assertListEqual(actual.value.tolist(), expected)
    self.assertEqual(actual.unit, "m")

  def testOutline_visualizes(self):
    region = Region(dims=Vec2D(5, 2, "arcsec"), center=Vec2D(7, 8, "arcsec"))
    perim = region.outline.value
