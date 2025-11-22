from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property

from matplotlib.backend_bases import MouseEvent, KeyEvent

from mirage.lens_analysis.result import ExperimentResult, SimulationResult
from mirage.util import VariantKey, Vec2D

@dataclass
class VizState:
    experiment: ExperimentResult
    variant_key_index: int = 0
    layers: list[(str, bool)] = field(default_factory=list)

    @cached_property
    def _variant_keys(self) -> list[VariantKey]:
        return self.experiment.keys

    @property
    def simulation_result(self) -> SimulationResult:
        return self.experiment.simulation(self._variant_keys[self.variant_key_index])

    @property
    def variant_key(self) -> VariantKey:
        return self._variant_keys[self.variant_key_index]

class Panel(Enum):
    LINE = "LINE"
    IMAGE = "IMAGE"


@dataclass
class VizEvent:
    panel: Panel
    screen_pos: Vec2D
    name: str
    mouse_event: MouseEvent | None = None
    key_event: KeyEvent | None = None


