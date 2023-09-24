from multiprocessing import Process
import logging
import zipfile
from typing import Any
import yaml
import io
import pickle
import os
import sys

import numpy as np

from mirage.calc.dask_engine import DaskEngine
from mirage.sim import SimulationBatch
from mirage.util import ResultFileManager, DuplexChannel, ClusterProvider, Dictify, Stopwatch

logger = logging.getLogger(__name__)


class BatchRunner:

  def __init__(
      self,
      simulation_batch: SimulationBatch,
      output_filename: str,
      cluster_provider: ClusterProvider,
  ):
    self.simulation_batch: SimulationBatch = simulation_batch
    self.output_filename: str = output_filename
    self.cluster_provider = cluster_provider

  @staticmethod
  def _engine_main(
      simulation_batch: SimulationBatch, channel: DuplexChannel, cluster_provider: ClusterProvider
  ):
    try:
      engine = DaskEngine(event_channel=channel, cluster_provider=cluster_provider)
      engine.blocking_run_simulation(simulation_batch)
      logger.info("Terminating Engine")
    except Exception as e:
      channel.close()
      logger.error("Engine Encountered an error: ")
      raise e

  def start(self):
    timer = Stopwatch()
    timer.start()
    send, recv = DuplexChannel.create(10)

    engine_process = Process(
        name="EngineProcess",
        target=BatchRunner._engine_main,
        args=(self.simulation_batch, send, self.cluster_provider),
    )

    engine_process.start()  # This starts the engine in a separate process
    serializer = ResultFileManager(self.output_filename, "x")
    serializer.dump_simulation(self.simulation_batch)
    flag = True
    try:
      while flag:
        evt = recv.recv_blocking()
        if evt.closed or evt.empty:
          logger.info("EngineProcess Closed. Saving and quiting")
          flag = False
        else:
          reducer = evt.value
          serializer.dump_result(reducer)
    except Exception as e:
      logger.error("Encountered Error!")
      logger.error(str(e))
    finally:
      serializer.close()
      logger.info("Result saved to %s", self.output_filename)
      engine_process.join()  # After UI is closed, gracefully terminate engine process
      timer.stop()
      logger.info("Total Runtime: %ss", timer.total_elapsed_seconds())
