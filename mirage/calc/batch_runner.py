from multiprocessing import Process
import logging
import zipfile
from typing import Any
import yaml
import io
import pickle
import os
import sys

from matplotlib import pyplot as plt
import numpy as np

from mirage.calc.engine import Engine
from mirage.sim import Simulation
from mirage.util import ResultFileManager, DuplexChannel

logger = logging.getLogger(__name__)


class BatchRunner:

  def __init__(self, simulation: Simulation, output_filename: str):
    self.simulation: Simulation = simulation.copy()
    self.output_filename: str = output_filename

  @staticmethod
  def _engine_main(simulation: Simulation, channel: DuplexChannel):
    try:
      engine = Engine(event_channel=channel)
      engine.blocking_run_simulation(simulation)
      logger.info("Terminating Engine")
    except Exception as e:
      channel.close()
      logger.error("Engine Encountered an error: ")
      raise e

  def start(self):
    send, recv = DuplexChannel.create(3)

    engine_process = Process(
        name="EngineProcess",
        target=BatchRunner._engine_main,
        args=(self.simulation, send),
    )

    engine_process.start()  # This starts the engine in a separate process
    evt = recv.recv_blocking()
    if evt.closed or evt.empty:
      logger.info(
          "EngineProcess returned code indicating the thread closed. No result is saved."
      )
    else:
      reducer = evt.value
      serializer = ResultFileManager(self.output_filename, "x")
      serializer.dump_simulation(self.simulation)
      serializer.dump_result(reducer)
      serializer.close()
    engine_process.join()  # After UI is closed, gracefully terminate engine process
