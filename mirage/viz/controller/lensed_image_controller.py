from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from astropy import units as u

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.widgets import AxesWidget, Button
import numpy as np

from mirage.viz.window import VizWindow, MirageAxes
from mirage.calc.reducers import LensedImageReducer
from mirage.viz.viz_state import VizState, VizEvent, Panel
from mirage.viz.controller import Controller
from mirage.util import Index2D, VariantKey, Vec2D

class LensedImageController(Controller):
    def __init__(self, reducer_name: str | None = None) -> None:
        Controller.__init__(self)
        self._reducer_name = reducer_name
        self.reset()

    @property
    def supported_reducers(self) -> list[type[Reducer]]:
        return [LensedImageReducer]

    def reset(self) -> None:
        self.request_draw()

    def draw(self, state: VizState, window: VizWindow) -> Iterable[Artist]:
        reducer = self.find_reducer(state, MagnificationMapReducer, reducer_name = self._reducer_name)

    def bind_widgets(self, axes: Axes, state: VizState) -> list[AxesWidget]:
        pass

    def on_event(self, state: VizState, event: VizEvent) -> bool:
        pass
