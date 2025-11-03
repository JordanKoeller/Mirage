import os
import yaml  # type: ignore
import zipfile
import io
import pickle
from typing import Union, Dict, Any, Literal, Optional
import logging

from mirage.calc import Reducer
from mirage.util import Dictify, VariantKey
from mirage.sim import Experiment


logger = logging.getLogger(__name__)


class ResultFileManager:
    """
    Encapsulates file I/O for the results of a batch job.

    Results files combine a :class:`Simulation` with the result of all its reducers in
    one file.

    Result files describe a a simulation completely and hermetically, meaning a result
    file could be used to re-compute a simulation and come to an identical result.
    Additionally,

    Because Result files contain all the outputs of a simulation, they can become quite
    large. Hence it is important that this class is used as it minimizes how much data must
    be loaded into memory at once when manipulating `Result` objects.


    Implementation Details
    =====================

    Under the hood, Results are just zip files, containing:

    +   A `manifest.yaml` that describes the contents of the zip file.
    +   The :class:`Simulation` object, serialized as a `.yaml` file.
    +   A `config.yaml` file with details of how the run was performed.
    +   A unique file for the output of each reducer.

    Most of these files are self-explanatory, however, there is one tricky part: getting
    the corresponding output for a specific reducer. This is handled by the
    `manifest.yaml` file. At a high level, the `manifest.yaml` is a mapping from a
    particular Reducer to the filename containing that reducer's output.

    When constructing a Result file, every time `dump_result` is called a unique ID for
    the reducer is computed using the `Reducer.key()` method. If a reducer is dumpd
    multiple times (meaning `Reducer.key()` produces an ID that is alloady present in
    the map), the value for that key is converted to a list and the new filename appended
    to that list.

    Generally speaking, filenames of outputs are equal to the (sanitized) `Reducer.key()`
    followed by `_1`, `_2`, etc for reducers with multiple outputs.

    """

    def __init__(self, filename: str, mode: Literal["x", "r"]):
        self.filename = filename
        self.mode = mode
        if mode == "x":
            if os.path.exists(self.filename):
                os.remove(self.filename)
        else:
            if not os.path.exists(self.filename):
                raise FileNotFoundError(self.filename)
        self.zip_archive = zipfile.ZipFile(self.filename, mode=mode)
        self.manifest: Dict[int, Dict[str, str]] = {}
        if mode == "r":
            self.manifest = self._load("manifest.yaml")  # type: ignore

    @classmethod
    def new_loader(cls, filename: str) -> "ResultFileManager":
        return cls(filename, "r")

    @classmethod
    def new_writer(cls, filename: str) -> "ResultFileManager":
        return cls(filename, "x")

    def dump_experiment(self, experiment: Experiment):
        self._write("experiment.yaml", experiment.to_dict())

    def load_simulation(self) -> Experiment:
        sim_dict: dict = self._load("experiment.yaml")  # type: ignore
        return Dictify.from_dict(Experiment, sim_dict)  # type: ignore

    def close(self):
        if self.mode == "x":
            self._write("manifest.yaml", self.manifest)
        self.zip_archive.close()

    def dump_result(self, reducer: Reducer, simulation_key: VariantKey):
        filename = self._insert_manifest_entry(reducer, simulation_key)
        self._write(filename, reducer.output)
        logger.debug(f"Simulation {simulation_key} Reducer {reducer.name} written to file.")

    def __len__(self) -> int:
        return len(self.manifest)

    def load_result(self, reducer_name: str, simulation_key: VariantKey) -> Reducer:
        sim_dict: dict[str, str] = self.manifest.get(str(simulation_key), {})
        filename: Optional[str] = sim_dict.get(reducer_name, None)
        if sim_dict is None:
            raise ValueError(
                f"Simulation of {simulation_key=} not recognized.\n Available "
                f"sims: {list(self.manifest.keys())}"
            )
        if filename is None:
            raise ValueError(
                f"'reducer_id' {reducer_name} not present in result manifest "
                f"for simulation {simulation_key}.\nAvailable ids: "
                f"{list(sim_dict.keys())}"
            )

        output = self._load(filename)  # type: ignore
        reducers = self.load_simulation()[simulation_key].reducers
        logger.warning("Has reducers %s" % str(reducers))
        for reducer in reducers:
            logger.warning("Has name %s" % reducer.name)
            if reducer.name == reducer_name:
                reducer.set_output(output)
                return reducer
        raise ValueError(
            f"Could not find reducer with "
            f"name={reducer_name} in Simulation {simulation_key}"
        )

    def _write(self, filename: str, data: Any):
        with self.zip_archive.open(filename, mode="w") as f:
            if filename.endswith("yaml"):
                string_io = io.StringIO()
                yaml.dump(data, string_io)
                f.write(bytes(string_io.getvalue(), "utf-8"))
            else:
                pickle.dump(data, f)

    def _load(self, filename: str) -> Union[dict, object]:
        with self.zip_archive.open(filename, mode="r") as f:
            if filename.endswith("yaml"):
                return yaml.load(f.read(), yaml.CLoader)
            else:
                return pickle.load(f)

    def _insert_manifest_entry(
        self, reducer: Reducer, simulation_key: VariantKey
    ) -> str:
        """
        Inserts a record into the manifest and returns the filename that should
        be used to dump the output
        """
        fname = f"{reducer.name.replace('/', '-')}_{simulation_key}.pickle"
        if simulation_key in self.manifest:
            self.manifest[str(simulation_key)][reducer.name] = fname
        else:
            self.manifest[str(simulation_key)] = {reducer.name: fname}
        return fname
