from unittest import TestCase

from astropy import units as u
import numpy as np

from mirage.calc.tracers import PointLensTracer
from mirage.util import PixelRegion, Vec2D, LabeledStopwatch
from mirage.model import Quasar, Starfield
from mirage.model.impl import PointLens
from mirage.model.initial_mass_function import Pooley2012
from mirage.calc.tracers.micro_tracer import _CpuTracerFn
from mirage.calc.tracers.micro_tracer_helper import (
  trace_bruteforce,
  trace_gravity_tree,
)


class TestPointLensTracer(TestCase):
  def setUp(self):
    self.tracer = PointLensTracer(u.Quantity(1e12, "solMass"))

  # def testTrace_success(self):
  #   region = PixelRegion(
  #     dims=Vec2D(25, 25, "arcsec"),
  #     center=Vec2D.zero_vector("arcsec"),
  #     resolution=Vec2D.unitless(500, 500),
  #   )
  #   output = self.tracer.trace(region)
  #   self.assertEqual(output.unit, u.arcsec)


class TestMicroTracer(TestCase):
  def testTrace_oneLargeStar_sameResultAsPointLenseTracer(self):
    point_lens = PointLens(
      quasar=Quasar(2.0, mass=u.Quantity(1e9, "solMass")),
      redshift=0.5,
      mass=u.Quantity(1e12, "solMass"),
    )
    region = PixelRegion(
      dims=Vec2D(5, 55, "arcsec"),
      center=Vec2D.zero_vector("arcsec"),
      resolution=Vec2D.unitless(500, 500),
    )
    tracer = point_lens.get_ray_tracer()
    sample_ray = region.pixels.value
    micro_tracer = _CpuTracerFn(True)
    micro_traced = micro_tracer.trace(
      sample_ray, 0.0, 0.0, np.array([1e12]), np.array([[0.0, 0.0]])
    )
    macro_traced = tracer.trace(region)
    for a, b in zip(
      micro_traced[:, :, 0:2].flatten().tolist(),
      macro_traced[:, :, 0:2].value.flatten().tolist(),
    ):
      # less than 1e-7 fractional difference
      self.assertLess(abs(a - b) / (a + b) / 2, 1e-7, f"{a} != {b}")

  # @unittest.skip
  # def testTrace_stressTest(self):
  #   tracers = [(trace_rays, ()), (micro_ray_trace, (1,))]
  #   watches = LabeledStopwatch()
  #   for t, args in tracers:
  #     with watches.timeit(t.__name__):
  #       self._stressTestTracer(t, *args)
  #   print("\n============ Runtimes ================")
  #   watches.print()

  # def testTrace_oneLargeStar_sameParityAsPointLensTracer(self):
  #   point_lens = PointLens(
  #     quasar=Quasar(2.0, mass=u.Quantity(1e9, "solMass")),
  #     redshift=0.5,
  #     mass=u.Quantity(1e12, "solMass"),
  #   )
  #   region = PixelRegion(
  #     dims=Vec2D(5, 5, "arcsec"),
  #     center=Vec2D.zero_vector("arcsec"),
  #     resolution=Vec2D.unitless(500, 500),
  #   )
  #   tracer = point_lens.get_ray_tracer()
  #   sample_ray = region.pixels.to(point_lens.theta_0).value
  #   micro_tracer = _CpuTracerFn(True)
  #   micro_traced = micro_tracer.trace(
  #     sample_ray, 0.0, 0.0, np.array([1e12]), np.array([[0.0, 0.0]])
  #   )
  #   macro_traced = tracer.trace(region)
  #   i = 0
  #   for a, b in zip(
  #     micro_traced[:, :, 2].flatten().tolist(),
  #     macro_traced[:, :, 2].value.flatten().tolist(),
  #   ):
  #     # less than 1e-7 fractional difference
  #     self.assertLess(abs(a - b), 1e-7, f"{i}: {a} != {b}")
  #     i += 1

  def testTrace_gravityTree_matchesBruteforce(self):
    region = PixelRegion(
      dims=Vec2D(-8, 8, "arcsec"),
      center=Vec2D.zero_vector("arcsec"),
      resolution=Vec2D.unitless(2, 2),
    )
    rays = region.pixels.value
    star_p = np.asfortranarray((np.random.rand(100, 2) - 0.5) * 40.0)
    star_m = np.asfortranarray(np.random.rand(100) * 10)
    traced_bf = trace_bruteforce(
      np.copy(rays), 0.5, 0.0, np.copy(star_m), np.copy(star_p), False, True
    )
    for err_factor in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
      print(f"{err_factor=}")
      traced_gt = trace_gravity_tree(
        np.copy(rays), 0.5, 0.0, np.copy(star_m), np.copy(star_p), err_factor
      )
      np.testing.assert_allclose(traced_gt, traced_bf, err_msg=f"Err={err_factor}")

  def _stressTestTracer(self, tracer_func, *args):
    region = PixelRegion(
      dims=Vec2D(5, 55, "arcsec"),
      center=Vec2D.zero_vector("arcsec"),
      resolution=Vec2D.unitless(2000, 2000),
    )
    sample_ray = region.pixels.value
    tracer_func(
      sample_ray,
      0.3,
      0.2,
      np.array([1e6, 2e6, 3e6] * 300),
      np.array([[0.0, 0.0], [-0.1, 0.2], [1.0, 2.3]] * 300),
      *args,
    )
