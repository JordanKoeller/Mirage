import argparse
import logging
import tempfile
import os
from typing import Literal, Optional
from functools import cached_property
import sys

from mirage.sim import Experiment
from mirage.util import (
  Stopwatch,
  init_multiprocessing_logger,
)
from mirage.calc import Engine
from mirage.io import ResultFileManager
from mirage import lens_analysis as la


class MirageMain:
  def __init__(self):
    self.parser = argparse.ArgumentParser()
    self._bind_arguments()
    self.args = self.parser.parse_args()
    self.configure_logger()

  def _bind_arguments(self):
    self.parser.add_argument(
      "-r",
      "--read_file",
      type=str,
      required=False,
      nargs=1,
      help="File to open in read-only mode. If running in batch mode (default), this should be a yaml file with an Experiment defined. If running in visualization mode, this should be a .zip file written by a previous invocation of Mirage.",
    )
    self.parser.add_argument(
      "-w",
      "--write",
      required=False,
      nargs=1,
      type=str,
      help="The file to write the results of the experiment to. The filename should have extension .zip or no extension (in which case .zip is automatically appended).",
    )
    self.parser.add_argument(
      "-l",
      "--logs_directory",
      type=str,
      required=False,
      nargs=1,
      help="Directory to save logs to. If not provided a temporary directory is chosen",
    )
    self.parser.add_argument(
      "-v",
      "--viz",
      action="store_true",
      help="If specified, launches Mirage in visualization mode.",
    )
    self.parser.add_argument("--debug", action="store_true", help="Log debug messages")
    self.parser.add_argument(
      "-f",
      "--force",
      action="store_true",
      help="If specified, overwrites output file if it already exists",
    )

  @cached_property
  def logfile(self) -> str:
    if self.args.logs_directory:
      directory = self.args.logs_directory[0]
    directory = os.path.join(tempfile.gettempdir(), "mirage", "logs")
    os.makedirs(directory, exist_ok=True)
    existing_files = os.listdir(directory)
    return os.path.join(directory, f"debug_{len(existing_files)}.log")

  def configure_logger(self):
    level = logging.DEBUG if self.args.debug else logging.INFO
    self.queue_handler = init_multiprocessing_logger(self.logfile, level)
    self.logger = logging.getLogger("mirage_main")
    self.logger.info("Writing logs to " + self.logfile)

  @property
  def run_mode(self) -> Literal["batch", "viz"]:
    if self.args.viz:
      return "viz"
    return "batch"

  @property
  def output_file(self) -> Optional[str]:
    if self.args.write:
      output_name = self.args.write[0]
      if not output_name.endswith(".zip"):
        output_name = output_name + ".zip"
      if os.path.exists(output_name) and not self.overwrite:
        raise ValueError(
          f"Output file {output_name} already exists."
          " To overwrite, please try again with the '-f' flag"
        )
      return output_name
    return None

  @property
  def overwrite(self) -> bool:
    return bool(self.args.force)

  @property
  def read_file(self) -> str:
    if not self.args.read_file:
      return None

    read_file = self.args.read_file[0]
    if not os.path.exists(read_file):
      raise ValueError(f"File not found: {read_file}")
    return read_file

  def load_experiment(self) -> Optional[Experiment]:

    sim_file = self.read_file
    if not (sim_file.endswith(".yaml") or sim_file.endswith(".yml")):
      raise ValueError(
        f"Invalid filename {sim_file}. Sim files should have .yaml extension."
      )

    self.logger.info(f"Loading experiment from file: {sim_file}")

    with open(sim_file) as f:
      yaml_str = f.read()
      self.logger.debug("Contents:\n" + yaml_str)

    experiment = Experiment.from_yaml(sim_file)

    self.logger.info(f"Constructed Simulation of type: {type(experiment).__name__}")
    return experiment

  def run_viz_mode(self):
    from matplotlib.backends.qt_compat import QtWidgets

    filename = self.read_file
    if not filename.endswith(".zip"):
      filename = f"{filename}.zip"
    v, e = la.visualize(self.read_file)
    qapp = QtWidgets.QApplication.instance()
    if not qapp:
      qapp = QtWidgets.QApplication(sys.argv)
    qapp.exec()

  def run_batch_mode(self):
    if not main.output_file:
      raise ValueError("Cannot run batch-mode without an output file specified.")
    experiment = self.load_experiment()
    if experiment is None:
      raise ValueError("Cannot run batch-mode without an experiment specified.")

    timer = Stopwatch()
    timer.start()

    engine = Engine.create_default()

    serializer = ResultFileManager(self.output_file, "x")
    serializer.dump_experiment(experiment)
    try:
      for _ in range(engine.start_run_experiment(experiment)):
        result = engine.get_result(blocking=True)
        if result.cache_key:
          serializer.add_alias(result.cache_key, result.result_key)
          continue
        reporter = serializer.result_reporter(result.result_key)
        result.reducer.save(reporter)
    except EOFError:
      self.logger.info("Stream closed.")
      pass
    except Exception as e:
      self.logger.error("Encountered Error!")
      self.logger.error(str(e))
      raise e
    finally:
      serializer.close()
      self.logger.info("Result saved to %s", self.output_file)
      timer.stop()
      self.logger.info("Total Runtime: %ss", timer.total_elapsed_seconds())
      engine.stop()
      self.queue_handler.listener.stop()


if __name__ == "__main__":
  main = MirageMain()

  run_mode = main.run_mode

  if run_mode == "batch":
    main.logger.info("Running Batch Job")
    main.run_batch_mode()
    main.logger.info("Goodbye!")
  elif run_mode == "viz":
    main.run_viz_mode()
    main.logger.info("Goodbye!")
  else:
    raise NotImplementedError()
