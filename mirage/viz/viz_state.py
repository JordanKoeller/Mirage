from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property

from matplotlib.backend_bases import MouseEvent, KeyEvent

from mirage.calc import Engine
from mirage.lens_analysis.result import (
  ExperimentResult,
  SimulationResult,
  InMemorySimulationResult,
)
from mirage.util import VariantKey, Vec2D, Region, PixelRegion


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

  def simulation_result(
    self, variant_key: VariantKey | None = None
  ) -> SimulationResult:
    return self._experiment.simulation(
      variant_key or self.variant_keys[self._variant_key_index]
    )

  @property
  def variant_key(self) -> VariantKey:
    return self.variant_keys[self._variant_key_index]

  @property
  def source_region(self) -> Region:
    return Region(dims=self.simulation_result().simulation.source_region_dimensions)

  @property
  def lens_region(self) -> PixelRegion:
    return self.simulation_result().simulation.get_ray_bundle()

  def next_variant(self, rollover: bool = False) -> bool:
    """
    Advance to the next variant. Returns False if there are no more variants
    to advance to, in which case this method does nothing.
    """
    if rollover:
      self._variant_key_index = (self._variant_key_index + 1) % len(self.variant_keys)
      return True
    if self.variant_key == self.variant_keys[-1]:
      return False
    self._variant_key_index += 1
    return True

  def prev_variant(self, rollover: bool = False) -> bool:
    """
    Move to the previous variant. Returns False if already on the first
    variant, in which case this method does nothing.
    """
    if rollover:
      if self._variant_key_index == 0:
        self._variant_key_index = len(self.variant_keys) - 1
        return True
    if self.variant_key == self.variant_keys[0]:
      return False
    self._variant_key_index -= 1
    return True


@dataclass
class RealtimeParameters:
  """
  Dataclass for specifying parameters needed for real-time visualization.

  Parameters:
    engine: ("dask") - What type of engine to use for computation.
    save_to: (str | None) - A path where computed results should be saved. If
      provided any computed results are saved here in addition to them being
      visualized. If not specified, results are not saved to disk.
  """

  engine: str = "dask"
  save_to: str | None = None


@dataclass
class RealTimeVizState:
  realtime_parameters: RealtimeParameters
  simulation: Simulation

  engine: Engine
  _pending_results: int = 0
  _results: dict[str, Reducer] = field(default_factory=dict)

  layers: list[str] = field(default_factory=list)

  @property
  def realtime(self) -> bool:
    """
    Specifies if the VizState allows for real-time result calculation.
    """
    return True

  def simulation_result(self, variant: VariantKey | None = None) -> SimulationResult:
    return InMemorySimulationResult(
      self.simulation,
      self._results,
    )

  @cached_property
  def variant_keys(self) -> list[VariantKey]:
    return [VariantKey()]

  @property
  def variant_key(self) -> VariantKey:
    return self.variant_keys[0]

  @property
  def source_region(self) -> Region:
    return Region(dims=self.simulation.source_region_dimensions)

  @property
  def lens_region(self) -> Region:
    return self.simulation.get_ray_bundle()

  def next_variant(self) -> bool:
    return False

  def prev_variant(self) -> bool:
    return False

  # The following are for controlling real-time simulation

  def recompute(self, simulation: Simulation) -> bool:
    """
    Starts asynchronous computation of the specified simulation.

    Note this will not schedule simulation if a pending simulation
    calculation is still in flight.

    Returns a boolean indicating if the Simulation was scheduled or not.
    """
    self.ingest_results()
    if self._pending_results != 0:  # Still inflight work, can't start a new simulation.
      return False
    self.simulation = simulation
    self._pending_results = self.engine.start_run_simulation(self.simulation)
    if self._pending_results > 0:
      self._results = {}
      return True
    return False

  def ingest_results(self) -> None:
    """
    Consume any ready Simulation results from the Engine. This is non-blocking.

    Returns true if a new result is available.
    """
    if self._pending_results == 0:
      return False

    result_event = self.engine.get_result(blocking=False)
    if result_event is None:
      return False

    self._pending_results -= 1
    self._results[result_event.result.name] = result_event.result
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
