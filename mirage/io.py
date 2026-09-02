import os
from dataclasses import dataclass, field
import copy
import tempfile
import yaml  # type: ignore
import zipfile
import io
import pickle
from typing import Union, Any, Literal, Self
import logging
from functools import cache

from mirage.calc import Reducer, ResultKey
from mirage.util import VariantKey, LRUCache, DictifyMixin
from mirage.sim import Experiment


logger = logging.getLogger(__name__)


def _to_filename(result_key: str, fragment: str) -> str:
  return f"{result_key}/{fragment}" #  os.path.join(result_key, fragment)


@dataclass
class Manifest(DictifyMixin):
  # Map a ResultKey to the fragments within.
  entries: dict[str, set[str]] = field(default_factory=dict)

  # Maps from an aliased ResultKey to a ResultKey with the same result.
  aliases: dict[str, str] = field(default_factory=dict)

  def add_alias(self, new_result: ResultKey, alias_of: ResultKey) -> None:
    if str(alias_of) not in self.entries:
      raise ValueError(f"Could not find {alias_of=} in entries.")
    self.aliases[str(new_result)] = str(alias_of)

  def add_entry(self, result_key: ResultKey, fragment: str) -> str:
    fragments = self.entries.setdefault(str(result_key), set())
    if fragment in fragments:
      return ValueError("fragment already exists")
    fragments.add(fragment)
    return _to_filename(str(result_key), fragment)

  def get_filename(self, alias_key: ResultKey, fragment: str) -> str:
    de_aliased = self.aliases.get(str(alias_key), str(alias_key))
    if de_aliased not in self.entries:
      raise ValueError(f"Unrecongized result_key: {alias_key}")
    if fragment not in self.entries[de_aliased]:
      raise ValueError(f"Unrecongized fragment: {fragment}")
    return _to_filename(de_aliased, fragment)

  def de_alias(self, alias_key: ResultKey) -> str:
    return self.aliases.get(str(alias_key), str(alias_key))

  def to_dict(self) -> dict[str, Any] | list[Any]:
    return {
      "entries": {k: list(v) for k, v in self.entries.items()},
      "aliases": self.aliases,
    }

  @classmethod
  def from_dict(cls, dict_obj: dict[str, Any]) -> Self:
    return cls(
      entries={k: set(v) for k, v in dict_obj["entries"].items()},
      aliases=dict_obj["aliases"],
    )


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

  def __init__(
    self, filename: str, mode: Literal["x", "r"], cache: LRUCache | None = None
  ):
    self.filename = filename
    self.mode = mode
    if mode == "x":
      if os.path.exists(self.filename):
        os.remove(self.filename)
    else:
      if not os.path.exists(self.filename):
        raise FileNotFoundError(self.filename)
    self.zip_archive = zipfile.ZipFile(self.filename, mode=mode)
    self.manifest = Manifest()
    self.extracted_dir = None
    self._read_cache = cache
    if mode == "r":
      self.extracted_dir = tempfile.TemporaryDirectory()
      self.zip_archive.extractall(path=self.extracted_dir.name)
      self.manifest = Manifest.from_dict(self._load("manifest.yaml"))  # type: ignore

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
      self._write("manifest.yaml", self.manifest.to_dict())
    self.zip_archive.close()
    if self.extracted_dir:
      self.extracted_dir.cleanup()

  def __len__(self) -> int:
    return len(self.manifest)

  def __hash__(self, *args, **kwargs):
    return hash((self.filename, self.mode, id(self.manifest), id(self.zip_archive)))

  def load_result(self, reducer_name: str, simulation_key: VariantKey) -> Reducer:
    """
    Load a Reducer result from file and return the populated reducer.

    NOTE: This function caches the result indefinitely, which will cause issues for Experiment results.

    TODO: Add some cache eviction behavior so we can still load large results.
    """

    result_key = ResultKey(reducer_name, simulation_key)

    def _loader() -> tuple[Reducer, int]:
      reducers = self.load_experiment()[simulation_key].reducers
      for reducer in reducers:
        if reducer.name == reducer_name:
          reducer = copy.copy(reducer)
          reporter = self.result_reporter(result_key)
          reducer.load(reporter)
          return reducer, reporter.read_bytes
      raise ValueError(
        f"Could not find reducer with name={reducer_name} in Simulation {simulation_key}"
      )

    if self._read_cache is not None:
      return self._read_cache.lazy_get((self.manifest.de_alias(result_key),), _loader)
    return _loader()[0]

  def writer(self, result_key: ResultKey, fragment: str) -> io.IO:
    filename = self._insert_manifest_entry(result_key, fragment)
    return self.zip_archive.open(filename, mode="w")

  def reader(self, result_key: ResultKey, fragment: str) -> tuple[io.IO, int]:
    filename = self.manifest.get_filename(result_key, fragment)
    zip_info = self.zip_archive.getinfo(filename)
    reader = self.zip_archive.open(filename, mode="r")
    return reader, zip_info.file_size

  def result_reporter(self, result_key: ResultKey) -> "ReducerReporter":
    return ReducerReporter(result_key, self)

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

  def add_alias(self, from_result_key: ResultKey, to_result_key: ResultKey) -> None:
    self.manifest.add_alias(to_result_key, from_result_key)

  def _insert_manifest_entry(self, result_key: ResultKey, fragment: str) -> str:
    """
    Inserts a record into the manifest and returns the filename that should
    be used to dump the output
    """
    return self.manifest.add_entry(result_key, fragment)


class ReducerReporter:
  def __init__(
    self,
    result_key: ResultKey,
    result_file_manager: ResultFileManager,
  ) -> None:
    self._result_key = result_key
    self._result_file_manager = result_file_manager
    self.read_bytes = 0  # Number of bytes read

  def writer(self, filename: str) -> io.IO:
    return self._result_file_manager.writer(self._result_key, filename)

  def reader(self, filename: str) -> io.IO:
    buf, sz = self._result_file_manager.reader(self._result_key, filename)
    self.read_bytes += sz
    return buf
