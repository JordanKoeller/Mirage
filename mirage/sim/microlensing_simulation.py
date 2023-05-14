from dataclasses import dataclass, field
from typing import List, Optional
from copy import deepcopy
from functools import cached_property
import logging
import numpy as np

from mirage.model import LensingSystem, Starfield, TracingParameters, SourcePlane
from mirage.util import Region, Vec2D, PixelRegion
from mirage.sim import Simulation
from mirage.calc import Reducer, RayTracer
from mirage.calc.tracers import MicrolensingRayTracer

# Multiplied by the largest dimension of the ray bundle to get
# the radius of the starry region that should be populated.
STAR_REGION_FACTOR = 2
RAY_REGION_FACTOR = 2.6

logger = logging.getLogger(__name__)

@dataclass(kw_only=True)
class MicrolensingSimulation(Simulation):
  """
  Simulates a Microlensed situation

  Parameters:
  + lensing_system (LensingSystem): The large-scale model of the lens.
  + star_generator (StarGenerator): Used to generate stars for microlensing.
  + image_center (Vec2D): The position vector for the image to simulate, relative to the center of
                          the center of the large-scale model.
  + ray_count (int): Approximate number of rays to trace through the lens.
  + source_region_dimensions (Vec2D): The dimensions of the source region to model.
  + reducers (List[Reducer]): The reducers used to compute results from the simulation.
  """

  starfield: Starfield
  lensed_image_center: Vec2D
  ray_count: int
  source_region_dimensions: Vec2D

  def get_ray_tracer(self) -> RayTracer:
    starfield_radius = self.get_ray_bundle().dims.x * STAR_REGION_FACTOR # Units of rad 
    radius_dist = starfield_radius.value * self.lensing_system.lens_distance.to('lyr') # Units in rad
    starfield_area = np.pi * radius_dist * radius_dist
    starry_mass = self._tracing_parameters.starry_fraction * \
        self._tracing_parameters.convergence * \
        starfield_area * \
        self.lensing_system.critical_density

    smooth_matter = self._tracing_parameters.convergence * (1 - self._tracing_parameters.starry_fraction)

    logger.info(f"Total Starry Mass {starry_mass}")
    return MicrolensingRayTracer(
        self.starfield,
        starry_mass,
        starfield_radius,
        smooth_matter,
        self._tracing_parameters.shear)
    

  def get_ray_bundle(self) -> PixelRegion:
    conv, shear = self._tracing_parameters.convergence, self._tracing_parameters.shear
    ax_ratio = abs((1 - shear - conv)/(1 + shear - conv)) # In (0, 1]
    ray_dims: Vec2D = Vec2D(self.source_region_dimensions.x / ax_ratio,
                     self.source_region_dimensions.y) * RAY_REGION_FACTOR # type: ignore

    # See below for why this works
    resolution = self._get_pixels_resolution(ax_ratio)

    return PixelRegion(dims=ray_dims, resolution=resolution).to('rad')

  def get_reducers(self) -> List[Reducer]:
    return deepcopy(self.reducers)

  def _get_pixels_resolution(self, axis_ratio: float) -> Vec2D:
    """
    Creates a rectangular grid of pixels with the specified axis_ratio
    and a total number of pixels that approximates self.ray_count.

    The closeness of the approximation gets better as axis_ratio nears 1
    and self.ray_count gets larger. See the image in resources/pixels_generator.png,
    which shows %error as axis ratio and ray count changes. The image is generated
    by the testcase
    `test.test_mirage.test_sim.test_microlensing_simulation.TestMicrolensingSimulation.testGetRayBundle_table`

    """
    return Vec2D.unitless(
      np.floor(np.sqrt(self.ray_count / axis_ratio)),
      np.ceil(np.sqrt(self.ray_count * axis_ratio)))

  @property
  def source_plane(self) -> Optional[SourcePlane]:
    from matplotlib import pyplot as plt
    region = Region(
        dims=self.source_region_dimensions,
        center=Vec2D.zero_vector(self.source_region_dimensions.unit))

    return SourcePlane(
      quasar=deepcopy(self.lensing_system.quasar),
      source_region=region.to(self.lensing_system.theta_0))

  @cached_property
  def _tracing_parameters(self) -> TracingParameters:
    return self.lensing_system.microtracing_parameters(self.lensed_image_center)