import os
import copy
import tempfile
import yaml  # type: ignore
import zipfile
import io
import pickle
from typing import Union, Dict, Any, Literal, Optional
import logging
from functools import cache
import contextlib

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
    self.extracted_dir = None
    if mode == "r":
      self.extracted_dir = tempfile.TemporaryDirectory()
      self.zip_archive.extractall(path=self.extracted_dir.name)
      self.manifest = self._load("manifest.yaml")  # type: ignore

  @classmethod
  def new_loader(cls, filename: str) -> "ResultFileManager":
    return cls(filename, "r")

  @classmethod
  def new_writer(cls, filename: str) -> "ResultFileManager":
    return cls(filename, "x")

  def dump_experiment(self, experiment: Experiment):
    self._write("experiment.yaml", experiment.to_dict())

  @cache
  def load_experiment(self) -> Experiment:
    sim_dict: dict = self._load("experiment.yaml")  # type: ignore
    return Experiment.from_dict(sim_dict)

  def close(self):
    if self.mode == "x":
      self._write("manifest.yaml", self.manifest)
    self.zip_archive.close()
    if self.extracted_dir:
      self.extracted_dir.cleanup()

  def __len__(self) -> int:
    return len(self.manifest)

  def __hash__(self, *args, **kwargs):
    return hash((self.filename, self.mode, id(self.manifest), id(self.zip_archive)))

  @cache
  def load_result(self, reducer_name: str, simulation_key: VariantKey) -> Reducer:
    """
    Load a Reducer result from file and return the populated reducer.

    NOTE: This function caches the result indefinitely, which will cause issues for Experiment results.

    TODO: Add some cache eviction behavior so we can still load large results.
    """
    reducers = self.load_experiment()[simulation_key].reducers
    for reducer in reducers:
      if reducer.name == reducer_name:
        reducer = copy.copy(reducer)
        reporter = self.result_reporter(reducer.name, simulation_key)
        reducer.load(reporter)
        return reducer
    raise ValueError(
      f"Could not find reducer with name={reducer_name} in Simulation {simulation_key}"
    )

  def writer(self, reducer_name: str, variant_key: VariantKey, fragment: str) -> io.IO:
    filename = self._insert_manifest_entry(reducer_name, variant_key, fragment)
    return self.zip_archive.open(filename, mode="w")

  def reader(self, reducer_name: str, variant_key: VariantKey, fragment: str) -> io.IO:
    filename = (
      self.manifest.get(str(variant_key), {}).get(reducer_name, {}).get(fragment, None)
    )
    if filename is None:
      return ValueError(f"Fragment {fragment} does not exist.")
    return self.zip_archive.open(filename, mode="r")

  def result_reporter(
    self, reducer_name: str, variant_key: VariantKey
  ) -> "ReducerReporter":
    return ReducerReporter(reducer_name, variant_key, self)

  def _write(self, filename: str, data: Any):
    with self.zip_archive.open(filename, mode="w") as f:
      if filename.endswith("yaml"):
        string_io = io.StringIO()
        yaml.dump(data, string_io)
        f.write(bytes(string_io.getvalue(), "utf-8"))
      else:
        pickle.dump(data, f)

  #
  def _load(self, filename: str) -> Union[dict, object]:
    if self.extracted_dir:
      filename = os.path.join(self.extracted_dir.name, filename)
      if filename.endswith("yaml"):
        with open(filename, "r") as f:
          return yaml.load(f.read(), yaml.CLoader)
      with open(filename, "rb") as f:
        return pickle.load(f)
    with self.zip_archive.open(filename, mode="r") as f:
      if filename.endswith("yaml"):
        return yaml.load(f.read(), yaml.CLoader)
      else:
        return pickle.load(f)

  def _insert_manifest_entry(
    self, reducer_name: str, simulation_key: VariantKey, fragment: str
  ) -> str:
    """
    Inserts a record into the manifest and returns the filename that should
    be used to dump the output
    """
    simulation_key_str = str(simulation_key)
    fname = os.path.join(reducer_name.replace("/", "-"), simulation_key_str, fragment)
    if simulation_key_str in self.manifest:
      if reducer_name in self.manifest[simulation_key_str]:
        if fragment in self.manifest[simulation_key_str][reducer_name]:
          raise ValueError(f"Fragment {fragment} already exists")
        self.manifest[simulation_key_str][reducer_name][fragment] = fname
      else:
        self.manifest[simulation_key_str][reducer_name] = {fragment: fname}
    else:
      self.manifest[simulation_key_str] = {reducer_name: {fragment: fname}}
    return fname


class ReducerReporter:
  """ """

  def __init__(
    self,
    reducer_name: str,
    variant_key: VariantKey,
    result_file_manager: ResultFileManager,
  ) -> None:
    self._reducer_name = reducer_name
    self._variant_key = variant_key
    self._result_file_manager = result_file_manager

  def writer(self, filename: str) -> io.IO:
    return self._result_file_manager.writer(
      self._reducer_name, self._variant_key, filename
    )

  def reader(self, filename: str) -> io.IO:
    return self._result_file_manager.reader(
      self._reducer_name, self._variant_key, filename
    )
