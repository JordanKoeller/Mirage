from astropy import units as u

from . import MirageTestCase

from mirage.engine.MagmapReducer import MagmapReducer
from mirage.util import PixelRegion
from mirage.util import zero_vector, Vec2D

class TestMagmapReducer(MirageTestCase):

    def testQueryPointsProducesCorrectValues(self):
        radius = u.Quantity(1.2, 'rad')
        region = PixelRegion(zero_vector('rad'), Vec2D(100.0, 100.0, 'rad'), Vec2D(100, 100))
        expected_region = region.pixels.to('rad').value
        reducer = MagmapReducer(region, radius)
        points_generator = reducer.query_points()
        for i in range(100):
            for j in range(100):
                index, query = next(points_generator)
                coord, test_radius = query
                self.assertEqual(index, (i, j))
                self.assertEqual(test_radius, radius.value)
                self.assertAlmostEqual(coord[0], expected_region[i, j, 0])
                self.assertAlmostEqual(coord[1], expected_region[i, j, 1])
