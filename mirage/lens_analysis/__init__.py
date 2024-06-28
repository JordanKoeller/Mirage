from typing import Union, Optional

from .result import ExperimentResult, SimulationResult
from mirage.viz import Viz, VizWindow
from mirage.io import ResultFileManager

ACTIVE_WINDOW: Optional[VizWindow] = None


def load(filename: str) -> ExperimentResult:
    return ExperimentResult(ResultFileManager(filename, "r"))


def visualize(
    file_or_result: Union[str, SimulationResult],
    reducer_key: Optional[str] = None,
) -> Viz:
    global ACTIVE_WINDOW
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
    if ACTIVE_WINDOW is None:
        ACTIVE_WINDOW = VizWindow()
    visualizer = Viz.get_visualizer(reducer, ACTIVE_WINDOW)

    visualizer.show(reducer)
    return visualizer


__all__ = ["load", "visualize"]
