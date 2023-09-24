from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Optional, List, Type
import copy
import logging
from math import pi

from astropy import units as u
import yaml

from mirage.util import Region, Vec2D, PixelRegion, Dictify
from mirage.model import LensingSystem, SourcePlane
from mirage.calc import Reducer, RayTracer
from mirage.sim import VariancePreprocessor

# These values should be used to decide if a Microlensing model or Macrolensing model should be used
THRESHOLD_AREA = u.Quantity(100 * 100, "uas")
THRESHOLD_LOCAL_CURVATURE = 0.0001

# If more than THRESHOLD_STAR_COUNT stars the mass distribution is assumed smooth.
# # Individual star gravity is not computed.
THRESHOLD_STAR_COUNT = 100_000_000  # TODO: Utilize this value

logger = logging.getLogger(__name__)


@dataclass
class Simulation(ABC):
  lensing_system: LensingSystem
  reducers: List[Reducer] = field(default_factory=list)

  @staticmethod
  def from_dict(sim_dict: dict) -> 'Simulation':  # type: ignore
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

  def is_similar(self, other: 'Simulation') -> bool:
    """
    If `self` and `other` are similar, indicates that the two simulations have the same
    lensing model and will deflect rays equally.
    """
    return self.get_ray_tracer() == other.get_ray_tracer() and \
        self.get_ray_bundle() == other.get_ray_bundle()

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

  def copy(self) -> 'Simulation':
    return copy.deepcopy(self)


@dataclass
class SimulationBatch:

  simulations: List[Simulation]

  @classmethod
  def from_yaml_template(cls, yaml_template: str, preprocessor: Optional[VariancePreprocessor] = None):
    preprocessor = preprocessor if preprocessor else VariancePreprocessor()
    return cls([
      Simulation.from_dict(yaml.load(yaml_str, yaml.CLoader))
      for yaml_str in preprocessor.generate_variants(yaml_template)], yaml_template)

  def __len__(self) -> int:
    return len(self.simulations)

  def __getitem__(self, index: int):
    return self.simulations[index]
