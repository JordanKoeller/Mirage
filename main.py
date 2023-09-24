import argparse
import logging
import tempfile
import os
import sys
from typing import Literal, Optional
from functools import cached_property
import yaml  # type: ignore

from mirage.sim import Simulation, SimulationBatch
from mirage.util import Dictify, ClusterProvider, LocalClusterProvider
from mirage.calc import reducers
from mirage.calc.batch_runner import BatchRunner

logger = logging.getLogger("mirage_main")


class MirageMain:

  def __init__(self):
    self.parser = argparse.ArgumentParser()
    self._bind_arguments()
    self.args = self.parser.parse_args()
    self.configure_logger()

  def _bind_arguments(self):
    a = self.parser
    self.parser.add_argument(
        "-r",
        "--read_sim",
        type=str,
        required=False,
        nargs=1,
        help="Simulation yaml file to load",
    )
    self.parser.add_argument(
        "-c",
        "--cluster",
        required=False,
        nargs=1,
        type=str,
        default="cluster.yaml",
        help="Filename containing the cluster spec to use. If not provided, the program"
        "looks for a `cluster.yaml` in the current directory. Otherwise, a default"
        "cluster on localhost is provisioned",
    )
    self.parser.add_argument(
        "-w",
        "--write",
        required=False,
        nargs=1,
        type=str,
        help="The file to write the results of the simulation_batch to."
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
        "-v", "--viz", action="store_true", help="Launch in visualization mode"
    )
    self.parser.add_argument(
        "-i",
        "--interractive",
        action="store_true",
        help="Launch in interractive mode",
    )
    self.parser.add_argument("--debug", action="store_true", help="Log debug messages")
    self.parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="If specified, overwirtes output file if it already exists",
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
    logging.basicConfig(
        level=logging.DEBUG if self.args.debug else logging.INFO,
        format="%(asctime)s [%(processName)15s] %(levelname)5s - %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(self.logfile),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger.info("Writing logs to " + self.logfile)

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
  def cluster_provider(self) -> ClusterProvider:
    try:
      cluster = Dictify.from_yaml(ClusterProvider, self.args.cluster[0])  # type: ignore
      logger.info(
          f"Constructed {type(cluster).__name__} cluster from file {self.args.cluster[0]}"
      )
      return cluster
    except FileNotFoundError:
      logger.info("No cluster config file found. Using default local cluster")
      return LocalClusterProvider()

  @property
  def overwrite(self) -> bool:
    return bool(self.args.force)

  def load_simulation(self) -> Optional[SimulationBatch]:
    if not self.args.read_sim:
      return None

    sim_file = self.args.read_sim[0]
    if not os.path.exists(sim_file):
      raise ValueError(f"File not found: {sim_file}")

    logger.info(f"Loading simulation_batch from file: {sim_file}")

    with open(sim_file) as f:
      yaml_str = f.read()
      logger.debug("Contents:\n" + yaml_str)

      simulation_batch = SimulationBatch.from_yaml_template(yaml_str)

      logger.info(f"Constructed Simulation of type: {type(simulation_batch).__name__}")
      return simulation_batch


if __name__ == "__main__":
  main = MirageMain()

  simulation_batch = main.load_simulation()
  run_mode = main.run_mode

  if run_mode == "batch" and simulation_batch and main.output_file:
    logger.info("Running Batch Job")
    batch_runner = BatchRunner(
      simulation_batch, main.output_file, main.cluster_provider)
    batch_runner.start()
    logger.info("Goodbye!")

  if run_mode == "interractive":
    raise NotImplementedError()

  if run_mode == "viz" and simulation_batch:
    from mirage.viz import VizRunner

    if len(simulation_batch) > 1:
      raise ValueError(
        f"Viz tool can only be used with only one loaded Simulation but %d found", len(simulation_batch))

    logger.info("Running visualization")
    viz_runner = VizRunner(simulation_batch.simulations[0])
    viz_runner.start()
    logger.info("Goodbye!")
