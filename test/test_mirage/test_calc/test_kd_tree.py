from unittest import TestCase, skip
from datetime import datetime

import numpy as np
from astropy import units as u

from mirage.calc import KdTree, RustKdTree, PyKdTree
from mirage.util import Vec2D


@skip("Medium Test")
class TestKdTreePerformance(TestCase):

  def setUp(self):
    self.dataset = u.Quantity(np.random.rand(4, 4, 2), "arcsec")
    self.pos = Vec2D.zero_vector("arcsec")
    self.radius = u.Quantity(0.01, "arcsec")
    print("Time trial starting")

  def tearDown(self):
    print("Time trial complete\n")

  def testKdTreeConstruction(self):
    self.timeit(lambda: KdTree(self.dataset), "Py.__init__")
    self.timeit(lambda: RustKdTree(self.dataset), "Rust.__init__")

  def testKdTreeQuery(self):
    pytree = KdTree(self.dataset)
    self.timeit(lambda: pytree.query_rays(self.pos, self.radius), "Py.query")
    rstree = RustKdTree(self.dataset)
    self.timeit(lambda: rstree.query_rays(self.pos, self.radius), "Rs.query")

  def testKdTreeQueryCount(self):
    pytree = KdTree(self.dataset)
    self.timeit(
        lambda: pytree.query_count(
            self.pos.x.value, self.pos.y.value, self.radius.value
        ),
        "Py.query_count",
    )
    rstree = RustKdTree(self.dataset)
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
      py_times.append(self.getConstructionTime(s, KdTree))
      rs_times.append(self.getConstructionTime(s, RustKdTree))
    from matplotlib import pyplot as plt

    plt.title("Construction Performance Trend (Py in Red)")
    plt.plot(np.array(scales) ** 2, py_times, "r")
    plt.plot(np.array(scales) ** 2, rs_times, "b")
    plt.show()

  def testPerformanceQueryTrend(self):
    scales = [2, 32, 128, 512, 1024, 1600, 2048, 3000]
    py_times = []
    rs_times = []
    for s in scales:
      py_times.append(self.getQueryTime(s, KdTree))
      rs_times.append(self.getQueryTime(s, RustKdTree))
    from matplotlib import pyplot as plt

    plt.title("Query Performance Trend (Py in Red)")
    plt.plot(np.array(scales) ** 2, py_times, "r")
    plt.plot(np.array(scales) ** 2, rs_times, "b")
    plt.show()

  def getConstructionTime(self, size: int, Tree) -> float:
    dataset = u.Quantity(np.random.rand(size, size, 2), "arcsec")
    return self.timeit(lambda: Tree(dataset), f"Construction Time {Tree.__name__}")

  def getQueryTime(self, size: int, Tree) -> float:
    dataset = u.Quantity(np.random.rand(size, size, 2), "arcsec")
    tree = Tree(dataset)
    return self.timeit(
        lambda: tree.query_rays(Vec2D(0.2, 0.1, "arcsec"), u.Quantity(0.06, "arcsec")),
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
