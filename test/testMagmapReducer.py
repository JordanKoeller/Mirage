import numpy as np

from .TestingHelpers import MirageTestCase
from mirage.util import PixelRegion, Vec2D, zero_vector

from mirage.reducers import MagmapReducer

class TestMagmapReducer(MirageTestCase):




    def testReducerIteratesCorrectly(self):
        reducer = self.getWithDims(2, 2)
        expected_ij = [
            [0, 0],
            [0, 1],
            [1, 0],
            [1, 1]
        ]
        index = 0
        reducer.start_iteration()
        while reducer.has_next_accumulator():
            acc = reducer.next_accumulator()
            self.assertEqual(expected_ij[index][0], reducer.active_key[0])
            self.assertEqual(expected_ij[index][1], reducer.active_key[1])
            index += 1
        self.assertEqual(index, 4)

    def testReducerAccumulatesValues(self):
        reducer = self.getWithDims(2, 2)
        counts = np.array([
            [5, 4],
            [9, 12]
        ], dtype=np.float64)
        reducer.start_iteration()
        while reducer.has_next_accumulator():
            acc = reducer.next_accumulator()
            i, j = reducer.active_key[0], reducer.active_key[1]
            for _ in range(int(counts[i, j])):
                print("Adding", i, j)
                acc.reduce_ray(reducer.pixels[0, 0])
            reducer.save_value(acc.get_result())
        value = reducer.value()
        for i in range(2):
            for j in range(2):
                self.assertEqual(counts[i,j], value[i,j])

    def testReducerMergesValues(self):
        reducer1 = self.getWithDims(2, 2)
        reducer2 = self.getWithDims(2, 2)
        counts1 = np.array([
            [5, 4],
            [9, 12]
        ], dtype=np.float64)
        counts2 = np.array([
            [2, 3],
            [18, 22]
        ], dtype=np.float64)
        reducer1 = self.runReducer(reducer1, counts1)
        reducer2 = self.runReducer(reducer2, counts2)
        merged = reducer1.merge(reducer2)
        values = merged.value()
        expected = counts1 + counts2
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(expected[i,j], values[i,j])

    def testReducerIsTransportable(self):
        reducer = self.getWithDims(2, 2)
        counts = np.array([
            [5, 4],
            [9, 12]
        ], dtype=np.float64)
        reducer = self.runReducer(reducer, counts)
        reducer_transport = reducer.transport()
        reducer_refresh = MagmapReducer.from_transport(reducer_transport)
        values = reducer_refresh.value()
        for i in range(2):
            for j in range(2):
                self.assertAlmostEqual(counts[i,j], values[i,j])

    def getWithDims(self, i, j):
        region = PixelRegion(
            zero_vector('uas'), Vec2D(1.0, 1.0, 'uas'), Vec2D(i, j, ''))
        return MagmapReducer(region, 1.0)

    def runReducer(self, reducer, counts):
        reducer.start_iteration()
        while reducer.has_next_accumulator():
            accumulator = reducer.next_accumulator()
            i, j = reducer.active_key[0], reducer.active_key[1]
            for _ in range(int(counts[i, j])):
                accumulator.reduce_ray(reducer.pixels[0, 0])
            reducer.save_value(accumulator.get_result())
        return reducer