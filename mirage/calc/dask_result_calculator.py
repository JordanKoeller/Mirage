from functools import partial
import math
import logging
from dataclasses import dataclass
import copy

import dask.bag as dask_bag
import numpy as np

from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree, RayTracer, ResultCalculator
from mirage.util import (
  PixelRegion,
  ClusterProvider,
  size_to_bytes,
  bytes_to_size,
)

logger = logging.getLogger(__name__)

PARTITION_SIZE_RANGE = ["10MB", "100MB"]
RAYS_PER_PARTITION = list(map(lambda s: size_to_bytes(s) / 16, PARTITION_SIZE_RANGE))


@dataclass
class _RaysWithRegion:
  region: PixelRegion
  rays: np.ndarray


def _ray_trace(simulation: Simulation, ray_tracer: RayTracer, region: PixelRegion):
  """
  Applies a RayTracer to a PixelRegion, returning the traced rays numpy array.
  """
  with simulation.special_units():
    return _RaysWithRegion(region, ray_tracer.trace(region))


def _to_kd_tree(simulation: Simulation, rays_with_region: _RaysWithRegion):
  """
  Packs a numy array or rays into a KdTree.
  """
  with simulation.special_units():
    return KdTree(rays_with_region.rays, rays_with_region.region)


def _apply_reducer(
  simulation: Simulation, reducer: Reducer, kd_tree: KdTree
) -> Reducer:
  """Reduce the specified KdTree with a reducer."""
  with simulation.special_units():
    reducable = copy.deepcopy(reducer)
    reducable.reduce(kd_tree)
    return reducable


def _merge_reducers(a: Reducer, b: Reducer) -> Reducer:
  """
  Merge two hydrated reducers, returning a new Reducer with the result.
  """
  return copy.deepcopy(a).merge(b)


@dataclass
class DaskResultCalculator(ResultCalculator):
  cluster_provider: ClusterProvider
  trees: object | None = None

  def initialize(self) -> None:
    self.cluster_provider.initialize()
    logger.info(f"Dask Cluster hosted at {self.cluster_provider.dashboard}")

  def __del__(self, *args, **kwargs) -> None:
    self.cluster_provider.close()

  def raytrace(self, simulation: Simulation) -> None:
    partition_size = self.cluster_provider.rays_per_partition
    with simulation.special_units():
      ray_tracer = simulation.get_ray_tracer()
      rays: PixelRegion = simulation.get_ray_bundle().to(
        simulation.lensing_system.theta_0
      )
    if partition_size < RAYS_PER_PARTITION[0] or partition_size > RAYS_PER_PARTITION[1]:
      logger.warning(
        f"ClusterProvider requested {partition_size} rays per partition, which falls outside"
        " of the recommended range. For optimal performance, each partition should"
        f" be in the range {RAYS_PER_PARTITION} rays ({PARTITION_SIZE_RANGE}) per partition."
      )
    num_rays = rays.num_pixels
    num_partitions = int(math.ceil(num_rays / partition_size))
    partition_mem_size = bytes_to_size(partition_size * 16)

    logger.info(f"Subdividing into {num_partitions} ({partition_mem_size}) partitions")
    self.trees = self.cluster_provider.client.persist(
      dask_bag.from_sequence(rays.subdivide(num_partitions))
      .map(partial(_ray_trace, simulation, ray_tracer))
      .map(partial(_to_kd_tree, simulation))
    )

  def apply_reducer(self, simulation: Simulation, reducer: Reducer) -> Reducer:
    if self.trees is None:
      raise ValueError("Called apply_reducer but trees have not been traced.")
    reduced_future = self.trees.map(partial(_apply_reducer, simulation, reducer)).fold(
      _merge_reducers
    )
    return self.cluster_provider.client.compute(reduced_future, sync=True)
