from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Optional, List, Self, Type, Self
import copy
import logging
from math import pi

from astropy import units as u

from mirage.util import Region, Vec2D, PixelRegion, Dictify
from mirage.model import LensingSystem, SourcePlane
from mirage.calc import Reducer, RayTracer

THRESHOLD_AREA = u.Quantity(100 * 100, "uas")
THRESHOLD_STAR_COUNT = 100_000_000  # TODO: Utilize this value
THRESHOLD_LOCAL_CURVATURE = 0.0001

logger = logging.getLogger(__name__)


@dataclass
class Simulation(ABC):
  lensing_system: LensingSystem
  reducers: List[Reducer] = field(default_factory=list)

  @staticmethod
  def from_dict(sim_dict: dict) -> Self:  # type: ignore
    from mirage.sim import MicrolensingSimulation, MacrolensingSimulation

    dict_fields = set(sim_dict.keys())
    macro_fields = {
        Dictify._to_pascal_case(f.name) for f in fields(MacrolensingSimulation)
    }
    micro_fields = {
        Dictify._to_pascal_case(f.name) for f in fields(MicrolensingSimulation)
    }
    micro_only_fields = micro_fields - macro_fields
    present_micro_fields = dict_fields & micro_only_fields
    logger.debug(f"Present Fields {dict_fields}")
    logger.debug(f"Micro-only Fields {micro_only_fields}")
    logger.debug(f"Macro Fields {macro_fields}")
    logger.debug(f"Present Micro Fields {present_micro_fields}")
    if present_micro_fields:
      micro_sim = Dictify.from_dict(MicrolensingSimulation, sim_dict)
      if micro_sim:
        return micro_sim  # type: ignore
      raise ValueError(
          "Tried to construct a MicrolensingSimulation but got None instead"
      )
    macro_sim = Dictify.from_dict(MacrolensingSimulation, sim_dict)
    if macro_sim:
      return macro_sim  # type: ignore
    raise ValueError("Tried to construct a MacrolensingSimulation but got None instead")

  @abstractmethod
  def get_ray_tracer(self) -> RayTracer:
    """
    Returns a reference to the :class:`LensingSystem` inside this `Simulation` instance.
    """

  @abstractmethod
  def get_ray_bundle(self) -> PixelRegion:
    """
    Returns the rays to trace.
    """

  @abstractmethod
  def get_reducers(self) -> List[Reducer]:
    """
    Returns the reducers to process during this simulation run.
    """

  @property
  def source_plane(self) -> Optional[SourcePlane]:
    return None

  def contains_reducer(self, klass: Type[Reducer]) -> bool:
    if not self.reducers:
      return False
    for reducer in self.reducers:
      if isinstance(reducer, klass):
        return True
    return False

  def copy(self) -> Self:
    return copy.deepcopy(self)
