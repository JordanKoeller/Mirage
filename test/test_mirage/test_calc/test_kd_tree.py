from unittest import TestCase
from datetime import datetime

import numpy as np
from astropy import units as u

from mirage.calc.kd_tree import PyKdTree, KdTree
from mirage.util import Vec2D


class TestKdTreePerformance(TestCase):

  def setUp(self):
    self.dataset = u.Quantity(np.random.rand(4, 4, 2), "arcsec")
    self.pos = Vec2D.zero_vector("arcsec")
    self.radius = u.Quantity(0.01, "arcsec")
    print("Time trial starting")

  def tearDown(self):
    print("Time trial complete\n")

  def testKdTreeConstruction(self):
    self.timeit(lambda: PyKdTree(self.dataset), "Py.__init__")
    self.timeit(lambda: KdTree(self.dataset), "Rust.__init__")

  def testKdTreeQuery(self):
    pytree = PyKdTree(self.dataset)
    self.timeit(lambda: pytree.query(self.pos, self.radius), "Py.query")
    rstree = KdTree(self.dataset)
    self.timeit(lambda: rstree.query(self.pos, self.radius), "Rs.query")

  def testKdTreeQueryCount(self):
    pytree = PyKdTree(self.dataset)
    self.timeit(
        lambda: pytree.query_count(
            self.pos.x.value, self.pos.y.value, self.radius.value
        ),
        "Py.query_count",
    )
    rstree = KdTree(self.dataset)
    self.timeit(
        lambda: rstree.query_count(
            self.pos.x.value, self.pos.y.value, self.radius.value
        ),
        "Rs.query_count",
    )

  def testPerformanceTrend(self):
    scales = [2, 32, 128, 512, 1024, 1600, 2048, 3000]
    py_times = []
    rs_times = []
    for s in scales:
      py_times.append(self.getConstructionTime(s, PyKdTree))
      rs_times.append(self.getConstructionTime(s, KdTree))
    from matplotlib import pyplot as plt

    plt.plot(np.array(scales) ** 2, py_times, "r")
    plt.plot(np.array(scales) ** 2, rs_times, "b")
    plt.show()

  def testPerformanceQueryTrend(self):
    scales = [2, 32, 128, 512, 1024, 1600, 2048, 3000]
    py_times = []
    rs_times = []
    for s in scales:
      py_times.append(self.getQueryTime(s, PyKdTree))
      # rs_times.append(self.getQueryTime(s, KdTree))
    from matplotlib import pyplot as plt

    plt.plot(np.array(scales) ** 2, py_times, "r")
    # plt.plot(np.array(scales) ** 2, rs_times, 'b')
    plt.show()

  def getConstructionTime(self, size: int, Tree) -> float:
    dataset = u.Quantity(np.random.rand(size, size, 2), "arcsec")
    return self.timeit(lambda: Tree(dataset), "")

  def getQueryTime(self, size: int, Tree) -> float:
    dataset = u.Quantity(np.random.rand(size, size, 2), "arcsec")
    tree = Tree(dataset)
    return self.timeit(lambda: tree.query_count(0, 0, 0.06), "")

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
