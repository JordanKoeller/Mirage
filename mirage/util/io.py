import os
import yaml
import zipfile
import io
import pickle
from typing import Union, Dict, List, Any, Self, Literal

from mirage.calc import Reducer
from mirage.sim import Simulation
from mirage.util import Dictify


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
    if mode == "x":
      if os.path.exists(self.filename):
        os.remove(self.filename)
    else:
      if not os.path.exists(self.filename):
        raise FileNotFoundError(self.filename)
    self.zip_archive = zipfile.ZipFile(self.filename, mode=mode)
    self.manifest: Dict = {}
    if mode == "r":
      self.manifest = self._load("manifest.yaml")  # type: ignore

  @classmethod
  def new_loader(cls, filename: str) -> Self:
    return cls(filename, "r")

  @classmethod
  def new_writer(cls, filename: str) -> Self:
    return cls(filename, "x")

  def dump_simulation(self, simulation: Simulation):
    self._write("simulation.yaml", Dictify.to_dict(simulation))

  def load_simulation(self) -> Simulation:
    sim_dict: dict = self._load("simulation.yaml")  # type: ignore
    return Simulation.from_dict(sim_dict)

  def close(self):
    self._write("manifest.yaml", self.manifest)
    self.zip_archive.close()

  def dump_result(self, reducer: Reducer):
    filename = self._insert_manifest_entry(reducer)
    self._write(filename, reducer)

  def load_result(self, reducer_id: str) -> Reducer:
    filename = self.manifest.get(reducer_id, None)
    if filename is None:
      raise ValueError(
          f"'reducer_id' {reducer_id} not present in result manifest."
          f"\n:Available ids: {list(self.manifest.keys())}"
      )

    return self._load(filename)  # type: ignore

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

  def _insert_manifest_entry(self, reducer: Reducer) -> str:
    """
    Inserts a record into the manifest and returns the filename that should
    be used to dump the output
    """
    reducer_path = reducer._get_parent_key()
    reducer_key = reducer.type_key()
    manifest_dict = self.manifest
    for reducer_name in reducer_path:
      if reducer_name not in manifest_dict:
        manifest_dict[reducer_name] = {}
      manifest_dict = manifest_dict[reducer_name]
    if reducer_key in manifest_dict:
      reducer_key = f"{reducer_key}_{len(manifest_dict)}"
    fname = os.path.join(*reducer_path, f"{reducer_key}.pickle")
    manifest_dict[reducer_key] = fname
    return fname
