from astropy import units as u

from . import MirageTestCase

from mirage.engine.reducers import MagmapReducer, MagnificationQuery
from mirage.util import PixelRegion
from mirage.util import zero_vector, Vec2D

class TestMagmapReducer(MirageTestCase):

    def getReducer(self):
        radius = u.Quantity(1.2, 'rad')
        region = PixelRegion(zero_vector('rad'), Vec2D(100.0, 100.0, 'rad'), Vec2D(100, 100))
        expected_region = region.pixels.to('rad').value
        reducer = MagmapReducer(region, radius)
        return reducer

    def testQueryPointsProducesCorrectValues(self):
        radius = u.Quantity(1.2, 'rad')
        region = PixelRegion(zero_vector('rad'), Vec2D(100.0, 100.0, 'rad'), Vec2D(100, 100))
        expected_region = region.pixels.to('rad').value
        reducer = MagmapReducer(region, radius)
        points_generator = reducer.query_points()
        for i in range(100):
            for j in range(100):
                query = next(points_generator)
                self.assertEqual(query.identifier, (i, j))
                self.assertEqual(query.radius, radius.value)
                self.assertAlmostEqual(query.x, expected_region[i, j, 0])
                self.assertAlmostEqual(query.y, expected_region[i, j, 1])
    
    def testMagnificationQuerySumsCorrectCount(self):
        query = MagnificationQuery((0, 0), 0.1, 0.2, 1.2)
        query.reduce_ray([0.1, 0.2])
        query.reduce_ray([0.1, 0.2])
        query.reduce_ray([0.1, 0.2])
        self.assertEqual(query.get_result(), 3)

    def testMagmapReducerIsCloneable(self):
        reducer = self.getReducer()
        reducer2 = reducer.clone_empty()
        for query in reducer.query_points():
            query.reduce_ray([0.1, 0.2])
            query.reduce_ray([0.1, 0.22])
            query.reduce_ray([0.1, 0.23])
            self.assertEqual(query.get_result(), 3)
            reducer.save_value(query.identifier, query.get_result())
        arr = reducer.value
        blank = reducer2.value
        self.assertIsNone(blank)
        for i in arr.flatten():
            self.assertEqual(i, 3)

    def testMagmapReducerIsMergable(self):
        reducer = self.getReducer()
        reducer2 = reducer.clone_empty()
        for q1, q2 in zip(reducer.query_points(), reducer2.query_points()):
            q1.reduce_ray([0.1, 0.2])
            q1.reduce_ray([0.1, 0.22])
            q1.reduce_ray([0.1, 0.23])
            q2.reduce_ray([0.1, 0.23])
            q2.reduce_ray([0.1, 0.23])
            self.assertEqual(q1.get_result(), 3)
            self.assertEqual(q2.get_result(), 2)
            reducer.save_value(q1.identifier, q1.get_result())
            reducer2.save_value(q2.identifier, q2.get_result())
        arr1 = reducer.value
        arr2 = reducer2.value
        tot = reducer.merge(reducer2).value
        for i, j, k in zip(arr1.flatten(), arr2.flatten(), tot.flatten()):
            self.assertEqual(i, 3)
            self.assertEqual(j, 2)
            self.assertEqual(k, 5)