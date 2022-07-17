from unittest import skip
import numpy as np
from astropy import units as u

from . import MirageTestCase
from mirage.engine import DaskCalculationDelegate, MicroCPUDelegate
from mirage.engine.micro_ray_tracer import ray_trace_singlethreaded as dask_trace
from mirage.engine.micro_ray_tracer import ray_trace
from mirage.calculator.ResultCalculator import ResultCalculator
from mirage.util import zero_vector, PixelRegion, Region

class TestDaskCalculationDelegate(MirageTestCase):

    def testDaskRayTraceFunctionEqualsCpuRayTraceFunction(self):
        parameters = self.microlensing_simulation.parameters
        rays = parameters.ray_region.to(parameters.theta_E).pixels.value
        stars = parameters.stars
        kap, _, gam = parameters.mass_descriptors
        dask_traced = dask_trace(rays, np.empty_like(rays), kap, gam, stars)
        cpu_traced = ray_trace(rays, np.empty_like(rays), kap, gam, 12, stars)
        self.assertListEqual(list(cpu_traced.flatten()), list(dask_traced.flatten()))

    def testDaskRayTracerGetsEquivalentTracedRays(self):
        cpu_delegate = MicroCPUDelegate()
        dask_delegate = DaskCalculationDelegate()
        parameters = self.microlensing_simulation.parameters
        cpu_rays = cpu_delegate._ray_trace(parameters)
        dask_delegate.reconfigure(parameters)
        dask_rays = dask_delegate.array.compute()
        self.assertAlmostEqual(cpu_rays, dask_rays, 1e-4)

    def testDaskRayTracerCanConstructKDTree(self):
        dask_delegate = DaskCalculationDelegate()
        parameters = self.microlensing_simulation.parameters
        dask_delegate.reconfigure(parameters)
        self.assertEqual(dask_delegate._dask_array.npartitions, len(dask_delegate._dask_kd_tree))
        tree = dask_delegate._dask_kd_tree[0].compute()

    def testDaskDelegateProducesAcurateMagmap(self):
        cpu_delegate = MicroCPUDelegate()
        dask_delegate = DaskCalculationDelegate()
        parameters = self.microlensing_simulation.parameters
        region = PixelRegion(zero_vector('rad'), parameters.source_plane.dimensions, self.microlensing_simulation['magmap'].resolution).to(parameters.eta_0)
        radius = parameters.quasar.radius.to(parameters.eta_0)
        dask_delegate.reconfigure(parameters)
        dask_result = dask_delegate.query_region(region, radius)
        cpu_delegate.reconfigure(parameters)
        cpu_result = cpu_delegate.query_region(region, radius)
        self.assertAlmostEqual(cpu_result.value, dask_result.value, 1e-4)
