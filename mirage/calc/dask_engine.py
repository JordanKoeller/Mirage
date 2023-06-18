from abc import ABC
from dataclasses import dataclass, field
from typing import Iterator, Optional
from multiprocessing import Queue
from multiprocessing.connection import Connection
import time
import math
import logging

from astropy import units as u
import dask.bag as dask_bag

from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree, RayTracer
from mirage.util import Vec2D, DuplexChannel, RepeatLogger, Stopwatch
from mirage.model import SourcePlane

logger = logging.getLogger(__name__)


@dataclass
class DaskEngine:
  event_channel: DuplexChannel
  parallelism_factor: int = 4

  def blocking_run_simulation(self, simulation: Simulation):
    with u.add_enabled_units([
        simulation.lensing_system.theta_0,
        simulation.lensing_system.xi_0,
        simulation.lensing_system.einstein_radius,
    ]):
      logger.info("Starting Simulation. Now ray tracing")
      ray_tracer = simulation.get_ray_tracer()
      rays_region = simulation.get_ray_bundle().to(simulation.lensing_system.theta_0)

      ray_regions = dask_bag.from_sequence(
          rays_region.subdivide(self.parallelism_factor)
      )

      traced_rays = ray_regions.map(DaskEngine._trace_map(simulation, ray_tracer))
      logger.info("Traced rays. Now Constructing KdTree")

      trees = traced_rays.map(DaskEngine._kd_tree_map(simulation)).persist()

      logger.info("Finished building KdTree. Now applying reducers")
      source_plane = simulation.source_plane
      for reducer in self.get_reducers(simulation):
        self.event_channel.recv()
        if self.event_channel.sender_closed:
          return  # Short circuit if event channel is closed
        mapped_reducers = trees.map(
            DaskEngine._reduce_map(simulation, source_plane, reducer)
        )
        merged_reducer = mapped_reducers.fold(lambda a, b: a.merge(b))
        hydrated_reducer = merged_reducer.compute()
        self.export_outcome(hydrated_reducer)
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
    def f(subregion):
      print("_trace_map")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        return ray_tracer.trace(subregion)

    return f

  @staticmethod
  def _kd_tree_map(simulation: Simulation):
    def f(traced):
      print("_kd_tree_map")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        return KdTree(traced)

    return f

  @staticmethod
  def _reduce_map(
      simulation: Simulation, source_plane: Optional[SourcePlane], reducer: Reducer
  ):
    def f(tree):
      print("_reduce_map")
      with u.add_enabled_units([
          simulation.lensing_system.theta_0,
          simulation.lensing_system.xi_0,
          simulation.lensing_system.einstein_radius,
      ]):
        reducer.reduce(tree, source_plane)
        return reducer

    return f

  @staticmethod
  def _merge_reducers(a: Reducer, b: Reducer):
    print("_merge_reducers")
    return a.merge(b)
