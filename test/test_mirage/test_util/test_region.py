from unittest import TestCase, skip

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

  def testSubdivide_perfectSquare_givesRegionAsNonOverlappingSubsets(self):
    region = PixelRegion(dims=Vec2D(4, 4, "m"), resolution=Vec2D.unitless(4, 4))
    expected_pixels = region.pixels
    subgrids = region.subdivide(4)  # 4 regions of 4 points each
    self.assertSubregionEqual(subgrids, region)

  def testSubdivide_rectangularSupergridRegion_success(self):
    region = PixelRegion(dims=Vec2D(4, 4, "m"), resolution=Vec2D.unitless(12, 12))
    expected_pixels = region.pixels
    subgrids = region.subdivide(6)  # 4 regions of 4 points each
    self.assertSubregionEqual(subgrids, region)

  def testSubdivide_rectangularRegionAndSupergrid_success(self):
    region = PixelRegion(dims=Vec2D(4, 4, "m"), resolution=Vec2D.unitless(12, 24))
    expected_pixels = region.pixels
    subgrids = region.subdivide(6)  # 4 regions of 4 points each
    self.assertSubregionEqual(subgrids, region)

  def testSubdivide_largeGrid_success(self):
    region = PixelRegion(dims=Vec2D(4, 4, "m"), resolution=Vec2D.unitless(30, 47))
    expected_pixels = region.pixels
    subgrids = region.subdivide(20)  # 4 regions of 4 points each
    self.assertSubregionEqual(subgrids, region)

  def assertSubregionEqual(self, subregions, expected_region):
    from matplotlib import pyplot as plt

    subregion_coords = []
    expected_coords = []
    expected_pixels = expected_region.pixels
    for s in subregions:
      pixels = s.pixels
      for x in range(pixels.shape[0]):
        for y in range(pixels.shape[1]):
          subregion_coords.append(list(pixels[x, y].value))

    for x in range(expected_pixels.shape[0]):
      for y in range(expected_pixels.shape[1]):
        expected_coords.append(list(expected_pixels[x, y].value))

    subregion_coords = np.array(subregion_coords)
    expected_coords = np.array(expected_coords)

    # for region in subregions:
    #   outline = region.outline
    #   plt.plot(outline[:, 0], outline[:, 1])
    # plt.plot(expected_coords[:, 0], expected_coords[:, 1], '.r')
    # plt.plot(subregion_coords[:, 0], subregion_coords[:, 1], '.b')
    # plt.show()

    for region in subregions:
      self.assertAlmostEqual(region.delta.x.value, expected_region.delta.x.value)
      self.assertAlmostEqual(region.delta.y.value, expected_region.delta.y.value)

    self.assertApproxListEquals(subregion_coords, expected_coords)

  def assertApproxListEquals(self, coords_a, coords_b):
    self.assertEqual(len(coords_a), len(coords_b))
    found = False
    for coord in coords_a:
      closest_b = self.find_closest_to(coord, coords_b)
      r = np.sqrt((coord[0] - closest_b[0]) ** 2 + (coord[1] - closest_b[1]) ** 2)
      if r < 1e-6:
        found = True
    if not found:
      self.assertTrue(False, f"Could not find equivalent coord to {coord}")

  def find_closest_to(self, coord, coords):
    min_dist = 1e6
    best_found = None
    for test_coord in coords:
      r = np.sqrt((test_coord[0] - coord[0]) ** 2 + (test_coord[1] - coord[1]) ** 2)
      if r < min_dist:
        best_found = test_coord
    return best_found
