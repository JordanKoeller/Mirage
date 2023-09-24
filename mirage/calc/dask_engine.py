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

from mirage.sim import Simulation, SimulationBatch
from mirage.calc import Reducer, KdTree, RayTracer
from mirage.util import Vec2D, DuplexChannel, RepeatLogger, Stopwatch, PixelRegion, ClusterProvider, size_to_bytes, bytes_to_size
from mirage.model import SourcePlane

logger = logging.getLogger(__name__)

PARTITION_SIZE_RANGE = ["10MB", "100MB"]
RAYS_PER_PARTITION = list(map(lambda s: size_to_bytes(s) / 16, PARTITION_SIZE_RANGE))


@dataclass
class DaskEngine:
  event_channel: DuplexChannel
  cluster_provider: ClusterProvider

  def blocking_run_simulation(self, simulation_batch: SimulationBatch):
    self.cluster_provider.initialize()
    logger.info("Starting Simulation. Now ray tracing")
    logger.info(f"Dask Cluster hosted at {self.cluster_provider.dashboard}")
    timer = Stopwatch()
    timer.start()
    try:
      for sim in simulation_batch.simulations:
        self._run_single_simulation(sim)
    except Exception as e:
      logger.error("Encountered Error")
      logger.error(str(e))
    finally:
      timer.stop()
      logger.info("Total Engine Elapsed Time: %ss", timer.total_elapsed_seconds())
      self.cluster_provider.close()
      self.event_channel.close()

  def _run_single_simulation(self, simulation: Simulation):
    with u.add_enabled_units([
        simulation.lensing_system.theta_0,
        simulation.lensing_system.xi_0,
        simulation.lensing_system.einstein_radius,
    ]):
      ray_tracer = simulation.get_ray_tracer()
      rays_region: PixelRegion = simulation.get_ray_bundle().to(
          simulation.lensing_system.theta_0
      )

      partition_size = self.cluster_provider.rays_per_partition

      if (
          partition_size < RAYS_PER_PARTITION[0]
          or partition_size > RAYS_PER_PARTITION[1]
      ):
        logger.warning(
            f"ClusterProvider requested {partition_size} per partition, which falls outside"
            " of the recommended range. For optimal performance, each partition should"
            f" be in the range {RAYS_PER_PARTITION}, or {PARTITION_SIZE_RANGE} in"
            " memory."
        )

      num_rays = rays_region.num_pixels
      num_partitions = int(math.ceil(num_rays / partition_size))
      partition_mem_size = bytes_to_size(partition_size * 16)

      logger.info(
          f"Subdividing into {num_partitions} ({partition_mem_size}) partitions"
      )

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
        logger.info(f"Has hydrated {type(hydrated_reducer)}")
        self.export_outcome(hydrated_reducer)

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
