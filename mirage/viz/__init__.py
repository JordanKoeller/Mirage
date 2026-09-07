"""
viz package.
=============

`viz` includes tools for visualizing results from simulations.

The `viz` package follows the MVC pattern:
    + The `Viz` object is a container for the three components and manages binding
      them, as needed.
    + The `VizWindow` makes the "View" part of MVC
    + The `Model` is a `VizState` instance. This is primarily a wrapper of an
      `ExperimentResult` with some additional control parameters.
    + The `Controller` is the most complicated part. Generally speaking, there should
      be a separate controller for each type of Reducer. Each Controller is registered
      in the `Viz` object, and controllable as a layer in the UI.

## The `VizWindow`

One standard `VizWindow` is provided, consisting of three parts:
    + An image / heatmap visualizer, that makes up the majority of the window.
    + A plot for visualizing line graphs.
    + A panel for input widgets, displaying selected values, etc.

## Controllers

Controllers are registered in the UI as togglable layers. When a `Viz` object is set up
a default controller for each reducer in the ExperimentResult is enabled. Additional
controllers can be added / removed programatically or via the UI.

"""

from .viz_settings import VizConfig
from .viz import Viz
from .window import VizWindow, MirageAxes
from .controller import (
  Controller,
  MagMapController,
  LightcurvesController,
  DebugController,
  LensedImageController,
)
from .viz_state import VizState, Panel, VizEvent, RealTimeVizState, RealtimeParameters

_CONTROLLERS = {
  "MagMapController": MagMapController,
  "LightcurvesController": LightcurvesController,
  "DebugController": DebugController,
  "MagMap": MagMapController,
  "Magmap": MagMapController,
  "Lightcurves": LightcurvesController,
  "Lightcurve": LightcurvesController,
  "Debug": DebugController,
  "LensedImageController": LensedImageController,
  "LensedImage": LensedImageController,
}


def create_layers(*layers: list[str | Controller]) -> list[Controller]:
  ret = []
  for layer in layers:
    if isinstance(layer, Controller):
      ret.append(layer)
      continue
    ret.append(_CONTROLLERS[layer]())
  return ret


__all__ = [
  "Viz",
  "VizState",
  "VizWindow",
  "Controller",
  "MagMapController",
  "Panel",
  "VizEvent",
  "LightcurvesController",
  "DebugController",
  "MirageAxes",
  "RealTimeVizState",
  "create_layers",
  "VizConfig",
  "RealtimeParameters",
]
