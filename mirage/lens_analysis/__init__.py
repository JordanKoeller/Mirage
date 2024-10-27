from typing import Union, Optional

from .result import ExperimentResult, SimulationResult
from mirage.viz import Viz, VizWindow
from mirage.io import ResultFileManager

def load(filename: str) -> ExperimentResult:
    """
    Load the result of a mirage Experiment from the specified filename.

    The result is loaded in a read-only fashion.
    """
    return ExperimentResult(ResultFileManager(filename, "r"))


def visualize(
    file_or_result: Union[str, SimulationResult],
    reducer_key: Optional[str] = None,
) -> Viz:
    result: SimulationResult = file_or_result  # type: ignore
    if isinstance(file_or_result, str):
        result = load(file_or_result)
    if reducer_key:
        reducer = result.get_reducer(reducer_key)
    else:
        reducers = result.simulation.get_reducers()
        if len(reducers) > 1:
            raise ValueError(
                "A reducer_key must be provided for simulations with more "
                "than one reducer"
            )
        reducer = reducers[0]
    reducer = result.get_reducer(reducer.name)
    window = VizWindow()
    visualizer = Viz.get_visualizer(reducer, window)

    visualizer.show(reducer)
    return visualizer


__all__ = ["load", "visualize"]
