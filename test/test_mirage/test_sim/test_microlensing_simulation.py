from unittest import TestCase, skip
from io import StringIO
import yaml
import json

from astropy.units import Quantity
import numpy as np

from mirage.sim import MicrolensingSimulation
from mirage.model import Quasar, Starfield
from mirage.model.initial_mass_function import WeidnerKroupa2004
from mirage.model.impl import PointLens
from mirage.util import Vec2D, Dictify


class TestMicrolensingSimulation(TestCase):

  def setUp(self):
    self.sim = MicrolensingSimulation(
        lensing_system=PointLens(
            quasar=Quasar(2.0), redshift=0.5, mass=Quantity(1e12, "solMass")
        ),
        lensed_image_center=Vec2D(0.2, 2.1, "arcsec"),
        ray_count=100_000_000,
        source_region_dimensions=Vec2D(1.2, 1.2, "arcsec"),
        starfield=Starfield(initial_mass_function=WeidnerKroupa2004(), seed=2),
    )

  def testGetRayBundle_success(self):
    axis_ratios = np.linspace(0.01, 1.0, 100)
    for expected_ratio in axis_ratios:
      resolution = self.sim._get_pixels_resolution(expected_ratio)
      actual_ratio = float(resolution.y.value) / float(resolution.x.value)
      self.assertAlmostEqual(actual_ratio, expected_ratio, 0.005)
      self.assertAlmostEqual(
          resolution.x.value * resolution.y.value, self.sim.ray_count, 0.005
      )

  @skip("Not a unit test")
  def testGetRayBundle_table(self):
    axis_ratios = np.linspace(0.01, 1, 5)[::-1]
    ray_counts = [100_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000]
    ray_count_axes = ["10^5", "10^6", "10^7", "10^8", "10^9"]
    from matplotlib import pyplot as plt

    data = []
    for expected_ratio in axis_ratios:
      row = []
      for ray_count in ray_counts:
        self.sim.ray_count = ray_count
        resolution = self.sim._get_pixels_resolution(expected_ratio)
        actual_count = resolution.x.value * resolution.y.value
        d = abs(actual_count - self.sim.ray_count)
        c = self.sim.ray_count
        pcnt_err = 100 - abs((d - c) / c * 100)
        row.append(pcnt_err)
      data.append(row)
    data = np.array(data)
    fig, ax = plt.subplots()
    im = ax.imshow(data)
    ax.set_xticks(np.arange(len(ray_count_axes)), labels=ray_count_axes)
    ax.set_yticks(np.arange(len(axis_ratios)), labels=axis_ratios)
    for i in range(len(axis_ratios)):
      for j in range(len(ray_counts)):
        text = ax.text(j, i, "%.3f%%" % data[i, j], ha="center", va="center", color="w")
    ax.set_title(f"Pcnt Error vs (ray_count, axis_ratio)")
    ax.set_xlabel("Ray Count")
    ax.set_ylabel("Axis Ratio")
    fig.tight_layout()
    plt.show()
    plt.show()

  def testToDict_onlyPrimitiveTypes(self):
    dict_repr = Dictify.to_dict(self.sim)
    json_repr = json.loads(json.dumps(dict_repr))
    string_io = StringIO()
    yaml_repr = yaml.dump(json_repr, string_io)
    string_io.seek(0)
    print(string_io.read())

  def assertAlmostEqual(self, first, second, pcnt_diff):
    delta = second - first
    pcnt = (delta / first) + (delta / second) / 2
    if pcnt > pcnt_diff:
      self.fail(f"Error of {pcnt} between {first} and {second} exceeds {pcnt_diff}")
