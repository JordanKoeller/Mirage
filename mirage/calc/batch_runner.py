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
from mirage.sim import Simulation
from mirage.util import ResultFileManager, DuplexChannel, LocalClusterProvider, RemoteClusterProvider

logger = logging.getLogger(__name__)


class BatchRunner:

  def __init__(self, simulation: Simulation, output_filename: str):
    self.simulation: Simulation = simulation.copy()
    self.output_filename: str = output_filename

  @staticmethod
  def _engine_main(simulation: Simulation, channel: DuplexChannel):
    try:
      # local_cluster = LocalClusterProvider(num_workers=10, worker_mem="2GiB")
      local_cluster = RemoteClusterProvider("localhost:8786")
      engine = DaskEngine(event_channel=channel, cluster_provider=local_cluster)
      engine.blocking_run_simulation(simulation)
      logger.info("Terminating Engine")
    except Exception as e:
      channel.close()
      logger.error("Engine Encountered an error: ")
      raise e

  def start(self):
    send, recv = DuplexChannel.create(10)

    engine_process = Process(
        name="EngineProcess",
        target=BatchRunner._engine_main,
        args=(self.simulation, send),
    )

    engine_process.start()  # This starts the engine in a separate process
    serializer = ResultFileManager(self.output_filename, "x")
    serializer.dump_simulation(self.simulation)
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
    finally:
      serializer.close()
      logger.info("Result saved to %s", self.output_filename)
      engine_process.join()  # After UI is closed, gracefully terminate engine process
