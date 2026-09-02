import argparse
import logging
import tempfile
import os
from typing import Literal, Optional
from functools import cached_property

from mirage.sim import Experiment
from mirage.util import (
  Stopwatch,
  init_multiprocessing_logger,
)
from mirage.calc import Engine
from mirage.io import ResultFileManager

_HELP_PROLOGUE = """
Mirage: A program for simulating and visualizing high-fidelity gravitational lensing
and microlensing.
"""

_HELP_EPILOGUE = """
In addition to command line arguments, additional configurations may be provided via
a `mirage.yaml` config file, located at `~/.config/mirage.yaml` by default, or at any
location specified via the MIRAGE_CONFIG_FILE environment variable.
"""


class MirageMain:
  def __init__(self):
    self.parser = argparse.ArgumentParser(
      description=_HELP_PROLOGUE,
      epilog=_HELP_EPILOGUE,
    )
    self._bind_arguments()
    self.args = self.parser.parse_args()
    self.configure_logger()

  def _bind_arguments(self):
    self.parser.add_argument(
      "-r",
      "--read_sim",
      type=str,
      required=False,
      nargs=1,
      help="Simulation yaml file to load",
    )
    self.parser.add_argument(
      "-w",
      "--write",
      required=False,
      nargs=1,
      type=str,
      help="The file to write the results of the experiment to."
      "Ignored if runing in interractive mode.",
    )
    self.parser.add_argument(
      "-l",
      "--logs_directory",
      type=str,
      required=False,
      nargs=1,
      help="directory to save logs to. If not provided a temporary directory is chosen",
    )
    self.parser.add_argument(
      "-ll",
      "--log_level",
      type=str,
      required=False,
      nargs=1,
      help="What logging level to capture. Defaults to INFO logs and higher.",
    )
    self.parser.add_argument(
      "-v",
      "--viz",
      action="store_true",
      help="Launch in visualization mode",
    )
    self.parser.add_argument(
      "-i",
      "--interractive",
      action="store_true",
      help="Launch in interractive mode",
    )
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
    log_level = logging.INFO
    if self.args.log_level:
      log_level = self.args.log_level[0]
    self.queue_handler = init_multiprocessing_logger(self.logfile, log_level)
    self.logger = logging.getLogger("mirage_main")
    self.logger.info("Writing logs to " + self.logfile)

  @property
  def run_mode(self) -> Literal["batch", "interractive", "viz"]:
    if self.args.viz:
      return "viz"
    if self.args.interractive:
      return "interractive"
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

  def load_experiment(self) -> Optional[Experiment]:
    if not self.args.read_sim:
      return None

    sim_file = self.args.read_sim[0]
    if not os.path.exists(sim_file):
      raise ValueError(f"File not found: {sim_file}")

    self.logger.info(f"Loading experiment from file: {sim_file}")

    with open(sim_file) as f:
      yaml_str = f.read()
      self.logger.debug("Contents:\n" + yaml_str)

    experiment = Experiment.from_yaml(sim_file)

    self.logger.info(f"Constructed Simulation of type: {type(experiment).__name__}")
    return experiment

  def run_batch_mode(self):
    """
    Executes Mirage in batch mode.

    This is the main entrypoint for running a batch Experiment. It takes care of creating
    an engine, loading in the Experiment from file, and executing all simulations / reducers.

    The results is saved out to the file specified via the --write flag.
    """
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
    except EOFError as e:
      self.logger.info("Stream closed.")
      pass
    except Exception as e:
      self.logger.error("Encountered Error!")
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
  else:
    raise NotImplementedError()
