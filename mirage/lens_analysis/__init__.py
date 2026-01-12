from typing import Union, Optional

from .result import ExperimentResult, SimulationResult
from mirage.viz import Viz, VizWindow, VizState, MagMapController, LightcurvesController
from mirage.io import ResultFileManager

def load(filename: str) -> ExperimentResult | SimulationResult:
    """
    Load the result of a mirage Experiment from the specified filename.

    The result file is loaded in read-only mode.
    """
    return ExperimentResult(ResultFileManager(filename, "r"))


def visualize(
    file_or_result: Union[str, ExperimentResult],
    layers: list[str] | None = None,
) -> Viz:
    result: ExperimentResult = file_or_result  # type: ignore
    if isinstance(file_or_result, str):
        result = load(file_or_result)
    viz_obj = Viz(
        model=VizState(result, 0),
        view=VizWindow(),
        controllers=[MagMapController()])
    viz_obj.show()
    return viz_obj


__all__ = ["load", "visualize"]
