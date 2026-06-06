from typing import Union, Optional
import os

from mirage.sim import Simulation, Experiment
from mirage.calc import get_or_create_engine
from .result import ExperimentResult, SimulationResult
from mirage.viz import Viz, VizWindow, VizState, MagMapController, LightcurvesController, DebugController, RealtimeParameters, Controller, create_layers, RealTimeVizState
from mirage.io import ResultFileManager

def load(filename: str) -> ExperimentResult | Experiment:
    """
    Load a mirage Experiment from the specified filename.

    Either an Experiment or ExperimentResult is returned, depending on what
    structure is included in the provided file.

    If an ExperimentResult, the result is loaded in read-only mode.
    """
    if not os.path.exists(filename):
        raise ValueError(f"File not found: {filename}")
    if filename.endswith(".zip"):
        return ExperimentResult(ResultFileManager(filename, "r"))

    return Experiment.from_yaml(filename)

def visualize(
    file_or_result: str | ExperimentResult,
    layers: list[str | Controller] | None = None,
    realtime_parameters: RealtimeParameters | None = None
) -> Viz:
    result: ExperimentResult = file_or_result  # type: ignore
    if isinstance(file_or_result, str):
        result = load(file_or_result)
    viz_obj = Viz(
        model=VizState(result, 0),
        view=VizWindow(),
        controllers=create_layers(*(layers or ["Debug", "Magmap"])),
    )
    viz_obj.show()
    return viz_obj, result

def visualize_realtime(
    file_or_result: str | ExperimentResult,
    layers: list[str | Controller] | None = None,
    realtime_parameters: RealtimeParameters  = RealtimeParameters(),
) -> Viz:
    result: ExperimentResult = file_or_result  # type: ignore
    if isinstance(file_or_result, str):
        result = load(file_or_result)
    return Viz(
        model=RealTimeVizState(
            realtime_parameters=realtime_parameters,
            simulation=result.simulations()[0][1],
            engine=get_or_create_engine()
        ),
        view=VizWindow(),
        controllers=create_layers(*(layers or ["Debug", "Magmap"])),
    )


__all__ = ["load", "visualize"]
