from typing import Optional, Any
from dataclasses import dataclass

from mirage.util.io import ResultFileManager
from mirage.calc import Reducer
from mirage.sim import Simulation


class Result:

  def __init__(self, filename: str):
    self._io: ResultFileManager = ResultFileManager(filename, "r")
    self._sim: Simulation = self._io.load_simulation()

  def get_reducer(self, reducer_id: str) -> Reducer:
    return self._io.load_result(reducer_id)

  @property
  def simulation(self):
    return self._sim
