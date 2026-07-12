from unittest import TestCase, skip
from datetime import datetime

import numpy as np
from astropy import units as u

from mirage.calc import KdTree, RustKdTree
from mirage.util import Vec2D


class TestKdTreePerformance(TestCase):
    def setUp(self):
        self.dataset = u.Quantity(
            np.array(np.random.rand(4, 4, 2), order="F"), "arcsec"
        )
        self.pos = Vec2D.zero_vector("arcsec")
        self.radius = u.Quantity(0.01, "arcsec")
        print("Time trial starting")

    def tearDown(self):
        print("Time trial complete\n")

    # def testKdTreeConstruction(self):
    #     print("testKdTreeConstruction")
    # self.timeit(lambda: KdTree(self.dataset), "Py.__init__")

    # def testKdTreeQueryCount(self):
    #     print("testKdTreeQueryCount")
    #     pytree = KdTree(self.dataset)
    #     self.timeit(
    #         lambda: pytree.query_count(
    #             self.pos.x.value, self.pos.y.value, self.radius.value
    #         ),
    #         "Py.query_count",
    #     )

    # def testPerformanceTrend(self):
    #     print("testPerformanceTrend")
    #     scales = [2, 32, 128, 512, 1024, 1600, 2048, 3000]
    #     py_times = []
    #     for s in scales:
    #         py_times.append(self.getConstructionTime(s, KdTree))
    #     from matplotlib import pyplot as plt
    #
    #     plt.title("Construction Performance Trend (Py in Red)")
    #     plt.plot(np.array(scales) ** 2, py_times, "r")
    #     plt.show()

    def testPerformanceQueryTrend(self):
        print("testPerformanceQueryTrend")
        scales = [
            2500,
            3000,
            3500,
            4000,
            4500,
            5000,
            5500,
            6000,
            6500,
            7000,
            7500,
            8000,
        ]
        py_times = []
        for s in scales:
            py_times.append(self.getQueryTime(s, KdTree))
        from matplotlib import pyplot as plt

        print("x= ", (np.array(scales) ** 2).tolist())
        print("py= ", py_times)
        plt.title("Query Performance Trend (Py in Red)")
        plt.plot(np.array(scales) ** 2, py_times, "r")
        plt.show()

    def getConstructionTime(self, size: int, Tree) -> float:
        print("getConstructionTime", size)
        dataset = u.Quantity(
            np.array(np.random.rand(size, size, 2), order="F"), "arcsec"
        )
        return self.timeit(lambda: Tree(dataset), f"Construction Time {Tree.__name__}")

    def getQueryTime(self, size: int, Tree) -> float:
        print("getQueryTime ", size)
        dataset = u.Quantity(
            np.array(np.random.rand(size, size, 2), order="F"), "arcsec"
        )
        tree = Tree(dataset, 1)
        return self.timeit(
            lambda: tree.query_count(0.2, 0.1, 0.01),
            f"Query Time {type(tree).__name__}",
        )

    def timeit(self, func, label):
        starttime = datetime.now()
        trials = 5
        for _ in range(trials):
            func()
        endttime = datetime.now()
        delta = endttime - starttime
        millisecs = (delta.total_seconds() * 1e6 + delta.microseconds) / 1000
        avg_ms = millisecs / trials
        print(f"{label} completed in t_mean={avg_ms} ms")
        return avg_ms
