from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property

from matplotlib.backend_bases import MouseEvent, KeyEvent

from mirage.lens_analysis.result import ExperimentResult, SimulationResult
from mirage.util import VariantKey, Vec2D, Region


@dataclass
class VizState:
    _experiment: ExperimentResult
    _variant_key_index: int = 0
    layers: list[str] = field(default_factory=list)

    @property
    def realtime(self) -> bool:
        """
        Specifies if the VizState allows for real-time result calculation.
        """
        return False

    @cached_property
    def variant_keys(self) -> list[VariantKey]:
        return self._experiment.keys

    @property
    def simulation_result(self) -> SimulationResult:
        return self._experiment.simulation(
            self.variant_keys[self._variant_key_index]
        )

    @property
    def variant_key(self) -> VariantKey:
        return self.variant_keys[self._variant_key_index]

    @property
    def source_region(self) -> Region:
        return Region(
            dims=self.simulation_result.simulation.source_region_dimensions)

    @property
    def lens_region(self) -> Region:
        return self.simulation_result.simulation.get_ray_bundle()

    def next_variant(self) -> bool:
        """
        Advance to the next variant. Returns False if there are no more variants
        to advance to, in which case this method does nothing.
        """
        if self.variant_key == self.variant_keys[-1]:
            return False
        self._variant_key_index += 1
        return True

    def prev_variant(self) -> bool:
        """
        Move to the previous variant. Returns False if already on the first
        variant, in which case this method does nothing.
        """
        if self.variant_key == self.variant_keys[0]:
            return False
        self._variant_key_index -= 1
        return True


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
