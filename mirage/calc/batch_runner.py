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
from mirage.util import DuplexChannel, Dictify

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
      logger.error("Engine Encountered an error: ")
      logger.error(f"{type(e).__name__}(): {e}")
      channel.close()

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
      magmap = np.log10(evt.value + 1)
      serializer = BatchSerializer(self.output_filename, self.simulation)
      serializer.save_result(magmap)
      serializer.close()
    engine_process.join()  # After UI is closed, gracefully terminate engine process


class BatchSerializer:

  def __init__(self, filename: str, simulation: Simulation):
    self.filename = filename
    self.simulation = simulation
    if os.path.exists(self.filename):
      os.remove(self.filename)
    self.zip_archive = zipfile.ZipFile(self.filename, mode="x")
    self.result_index = 0

  def close(self):
    with self.zip_archive.open("simulation.yaml", mode="w") as f:
      string_io = io.StringIO()
      yaml.dump(Dictify.to_dict(self.simulation), string_io)
      f.write(bytes(string_io.getvalue(), "utf-8"))
    self.zip_archive.close()

  def save_result(self, obj: Any):
    filename = f"result_{self.result_index}.result"
    with self.zip_archive.open(filename, mode="w") as f:
      pickle.dump(obj, f)
    self.result_index += 1
