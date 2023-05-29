from typing import Union, Optional

from .result import Result
from mirage.viz import Viz


def load(filename: str) -> Result:
  return Result(filename)


def visualize(
    file_or_result: Union[str, Result],
    reducer_key: Optional[str] = None,
    visualizer: Optional[Viz] = None,
) -> Viz:
  result: Result = file_or_result  # type: ignore
  if isinstance(file_or_result, str):
    result = load(file_or_result)
  if reducer_key:
    reducer = result.get_reducer(reducer_key)
  else:
    reducers = result.simulation.get_reducers()
    if len(reducers) > 1:
      raise ValueError(
          "A reducer_key must be provided for simulations with more than one reducer"
      )
    reducer = reducers[0]
  reducer = result.get_reducer(reducer.key)
  visualizer = visualizer or Viz.get_visualizer(reducer)
  visualizer.show(reducer)
  return visualizer
