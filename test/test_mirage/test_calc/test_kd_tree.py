from unittest import TestCase
from datetime import datetime

import numpy as np
from astropy import units as u

from mirage.calc.kd_tree import PyKdTree, KdTree


class TestKdTreePerformance(TestCase):

  def setUp(self):
    print("Time trial starting")

  def tearDown(self):
    print("Time trial complete\n")

  def testKdTreeConstruction(self):
    dataset = u.Quantity(np.random.rand(1000, 1000, 2), "arcsec")
    self.timeit(lambda: PyKdTree(dataset), "Py.__init__")
    self.timeit(lambda: KdTree(dataset), "Rust.__init__")

  def timeit(self, func, label):
    starttime = datetime.now()
    trials = 1
    for _ in range(trials):
      func()
    endttime = datetime.now()
    delta = endttime - starttime
    millisecs = (delta.total_seconds() * 1e6 + delta.microseconds) / 1000
    avg_ms = millisecs / trials
    print(f"{label} completed in t_mean={avg_ms} ms")
    return avg_ms
