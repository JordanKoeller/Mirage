from abc import ABC
from dataclasses import dataclass, field
from typing import Iterator, Optional
from multiprocessing import Queue
from multiprocessing.connection import Connection
import time
import math
import logging
import copy

from astropy import units as u
import dask
from dask.distributed import Client, LocalCluster
import dask.bag as dask_bag

from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree, RayTracer
from mirage.util import Vec2D, DuplexChannel, RepeatLogger, Stopwatch, PixelRegion, ClusterProvider
from mirage.model import SourcePlane

logger = logging.getLogger(__name__)

RAYS_PER_PARTITION = 8000000  # Equates to 128 MB / Partition


@dataclass
class DaskEngine:
  event_channel: DuplexChannel
  cluster_provider: ClusterProvider

  def blocking_run_simulation(self, simulation: Simulation):
    with u.add_enabled_units([
        simulation.lensing_system.theta_0,
        simulation.lensing_system.xi_0,
        simulation.lensing_system.einstein_radius,
    ]):
      self.cluster_provider.initialize()
      logger.info("Starting Simulation. Now ray tracing")
      logger.info(f"Dask Cluster hosted at {self.cluster_provider.dashboard}")
      ray_tracer = simulation.get_ray_tracer()
      rays_region = simulation.get_ray_bundle().to(simulation.lensing_system.theta_0)

      num_rays = rays_region.num_pixels

      num_partitions = 10 * int(math.ceil(num_rays / RAYS_PER_PARTITION))

      logger.info(f"Subdividing into {num_partitions} partitions")

      trees = (
          dask_bag.from_sequence(rays_region.subdivide(num_partitions))
          .map(DaskEngine._trace_map(simulation, ray_tracer))
          .map(DaskEngine._kd_tree_map(simulation))
      )

      trees = self.cluster_provider.client.persist(trees)

      source_plane = simulation.source_plane
      for reducer in self.get_reducers(simulation):
        self.event_channel.recv()
        if self.event_channel.sender_closed:
          return  # Short circuit if event channel is closed
        mapped_reducers = trees.map(
            DaskEngine._reduce_map(simulation, source_plane, reducer)
        )
        merged_reducer = mapped_reducers.fold(lambda a, b: a.merge(b))
        hydrated_reducer = self.cluster_provider.client.compute(
            merged_reducer, sync=True
        )
        self.export_outcome(hydrated_reducer)
      self.cluster_provider.close()
      self.event_channel.close()

  def get_reducers(self, simulation: Simulation) -> Iterator[Reducer]:
    """
    Generator that returns all reducers involved in this simulation
    """
    return iter(simulation.get_reducers())

  def export_outcome(self, outcome: object):
    """
    Save off a result of this simulation.
    #"""
    self.event_channel.send_blocking(outcome)

  # The following are definitions for mapping functions
  @staticmethod
  def _trace_map(simulation: Simulation, ray_tracer: RayTracer):
    def trace_rays(subregion: PixelRegion):
      # print(f"_trace_map subregion_dims={subregion.resolution}")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        return ray_tracer.trace(subregion)

    return trace_rays

  @staticmethod
  def _kd_tree_map(simulation: Simulation):
    def construct_kd_trees(traced):
      # print("_kd_tree_map")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        return KdTree(traced)

    return construct_kd_trees

  @staticmethod
  def _reduce_map(
      simulation: Simulation, source_plane: Optional[SourcePlane], reducer: Reducer
  ):
    def apply_reducer(tree):
      # print("_reduce_map")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        reducable = copy.deepcopy(reducer)
        reducable.reduce(tree, source_plane)
        return reducable

    return apply_reducer

  @staticmethod
  def _merge_reducers(a: Reducer, b: Reducer):
    # print("_merge_reducers")
    return copy.deepcopy(a).merge(b)
