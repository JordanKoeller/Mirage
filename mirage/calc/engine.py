from abc import ABC
from dataclasses import dataclass, field
from typing import Iterator
from multiprocessing import Queue
from multiprocessing.connection import Connection
import time
import math
import logging

from astropy import units as u

from mirage.sim import Simulation
from mirage.calc import Reducer, KdTree
from mirage.util import Vec2D, DuplexChannel, RepeatLogger, Stopwatch

logger = logging.getLogger(__name__)


@dataclass
class Engine:
  event_channel: DuplexChannel

  def blocking_run_simulation(self, simulation: Simulation):
    with u.add_enabled_units([
        simulation.lensing_system.theta_0,
        simulation.lensing_system.xi_0,
        simulation.lensing_system.einstein_radius,
    ]):
      logger.info("Starting Simulation. Now ray tracing")
      ray_tracer = simulation.get_ray_tracer()
      rays = simulation.get_ray_bundle().to(simulation.lensing_system.theta_0)

      traced_rays = ray_tracer.trace(rays)
      logger.info("Traced rays. Now Constructing KdTree")

      rays_tree = KdTree(traced_rays)

      logger.info("Finished building KdTree. Now applying reducers")
      stopwatch = Stopwatch()
      r_logger = RepeatLogger(10, logger)
      for reducer in self.get_reducers(simulation):
        self.event_channel.recv()
        if self.event_channel.sender_closed:
          return  # Short circuit if event channel is closed
        reducer.reduce(rays_tree, simulation.source_plane)
        self.export_outcome(reducer)
        stopwatch.start()
        if r_logger.log(f"Frame time = {stopwatch.avg_elapsed()} ms"):
          stopwatch.reset()
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
