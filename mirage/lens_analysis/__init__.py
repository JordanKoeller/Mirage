import os
from dataclasses import dataclass

from mirage.sim import Experiment
from mirage.calc import get_or_create_engine
from mirage.util import LRUCache
from .result import ExperimentResult
from mirage.viz import (
  Viz,
  VizWindow,
  VizState,
  RealtimeParameters,
  Controller,
  create_layers,
  RealTimeVizState,
  VizConfig,
)
from mirage.io import ResultFileManager
from mirage.settings import load_settings


def load(filename: str) -> ExperimentResult | Experiment:
  """
  Load a mirage Experiment from the specified filename.

  Either an Experiment or ExperimentResult is returned, depending on what
  structure is included in the provided file.

  If an ExperimentResult, the result is loaded in read-only mode.
  """
  viz_config = load_settings(VizConfig)
  if not os.path.exists(filename):
    raise ValueError(f"File not found: {filename}")
  if filename.endswith(".zip"):
    return ExperimentResult(
      ResultFileManager(filename, "r", LRUCache(viz_config.io_cache_size))
    )

  return Experiment.from_yaml(filename)


def visualize(
  file_or_result: str | ExperimentResult,
  layers: list[str | Controller] | None = None,
  realtime_parameters: RealtimeParameters | None = None,
) -> Viz:
  result: ExperimentResult = file_or_result  # type: ignore
  if isinstance(file_or_result, str):
    result = load(file_or_result)
  viz_config = load_settings(VizConfig)
  viz_obj = Viz(
    model=VizState(result, 0),
    view=VizWindow(),
    controllers=create_layers(*(layers or viz_config.default_layers)),
  )
  viz_obj.show()
  return viz_obj, result


def visualize_realtime(
  file_or_result: str | ExperimentResult,
  layers: list[str | Controller] | None = None,
  realtime_parameters: RealtimeParameters = RealtimeParameters(),
) -> Viz:
  result: ExperimentResult = file_or_result  # type: ignore
  if isinstance(file_or_result, str):
    result = load(file_or_result)
  return Viz(
    model=RealTimeVizState(
      realtime_parameters=realtime_parameters,
      simulation=result.simulations()[0][1],
      engine=get_or_create_engine(),
    ),
    view=VizWindow(),
    controllers=create_layers(*(layers or ["Debug", "LensedImageController"])),
  )


__all__ = ["load", "visualize"]
