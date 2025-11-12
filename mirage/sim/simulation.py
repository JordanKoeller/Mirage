from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Optional, List, Type, Any
import copy
import logging

from astropy import units as u
import yaml

from mirage.util import PixelRegion, Dictify, DelegateRegistry, ObjVariants, VariantKey, VariantDictify, DictifyMixin
from mirage.model import LensingSystem, SourcePlane
from mirage.calc import Reducer, RayTracer

# These values should be used to decide if a Microlensing model or Macrolensing model should be used
THRESHOLD_AREA = u.Quantity(100 * 100, "uas")
THRESHOLD_LOCAL_CURVATURE = 0.0001

# If more than THRESHOLD_STAR_COUNT stars the mass distribution is assumed smooth.
# # Individual star gravity is not computed.
THRESHOLD_STAR_COUNT = 100_000_000  # TODO: Utilize this value

logger = logging.getLogger(__name__)


@dataclass
class Simulation(DictifyMixin):
    lensing_system: LensingSystem
    reducers: List[Reducer] = field(default_factory=list)

    def __post_init__(self):
        with self.special_units():
            for reducer in self.reducers:
                reducer.initialize(self)

    @staticmethod
    def units_from_dict(sim_dict: dict):
        lensing_system: Optional[LensingSystem] = None
        for fieldname in sim_dict:
            if fieldname.startswith("LensingSystem"):
                subtype = DelegateRegistry.get_typedef(
                    LensingSystem, fieldname.split("_")[1]
                )
                lensing_system = Dictify.from_dict(subtype, sim_dict[fieldname])
        if lensing_system:
            return lensing_system.special_units()

    @staticmethod
    def from_dict(sim_dict: dict) -> "Simulation":  # type: ignore
        from mirage.sim import MicrolensingSimulation, MacrolensingSimulation

        dict_fields = set(sim_dict.keys())
        macro_fields = {
            Dictify._to_pascal_case(f.name)
            for f in fields(MacrolensingSimulation)
        }
        micro_fields = {
            Dictify._to_pascal_case(f.name)
            for f in fields(MicrolensingSimulation)
        }
        micro_only_fields = micro_fields - macro_fields
        present_micro_fields = dict_fields & micro_only_fields
        with Simulation.units_from_dict(sim_dict):
            if present_micro_fields:
                micro_sim = Dictify.from_dict(
                    MicrolensingSimulation, sim_dict, False
                )
                if micro_sim:
                    return micro_sim  # type: ignore
                raise ValueError(
                    "Tried to construct a MicrolensingSimulation but got None instead"
                )
            macro_sim = Dictify.from_dict(
                MacrolensingSimulation, sim_dict, False
            )
            if macro_sim:
                return macro_sim  # type: ignore
            raise ValueError(
                "Tried to construct a MacrolensingSimulation but got None instead"
            )

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

    def is_similar(self, other: "Simulation") -> bool:
        """
        If `self` and `other` are similar, indicates that the two simulations
        have the same lensing model and will deflect rays equally.
        """
        return (
            self.get_ray_tracer() == other.get_ray_tracer()
            and self.get_ray_bundle() == other.get_ray_bundle()
        )

    @property
    def source_plane(self) -> Optional[SourcePlane]:
        return None

    def special_units(self):
        """
        Returns a context-object with special lens-specific units.
        """
        return self.lensing_system.special_units()

    def contains_reducer(self, klass: Type[Reducer]) -> bool:
        if not self.reducers:
            return False
        for reducer in self.reducers:
            if isinstance(reducer, klass):
                return True
        return False

    def copy(self) -> "Simulation":
        return copy.deepcopy(self)

class Experiment(ObjVariants[Simulation]):

    def simulations(self) -> list[tuple[VariantKey, Simulation]]:
        return list(self._objs.items())

    @classmethod
    def from_dict(cls, dict_obj: dict[str, Any]) -> 'Experiment':
        experiment = VariantDictify.from_dict(Simulation, dict_obj)
        if experiment is None:
            raise ValueError("Failed to construct an experiement")
        return cls(
            list(experiment._variants.values()),
            experiment._objs,
            experiment._template)

    @classmethod
    def from_yaml(cls, yaml_filename: str) -> 'Experiment':
        with open(yaml_filename) as f:
            yaml_str = f.read()
            dict_obj = yaml.load(yaml_str, yaml.CLoader)
            return cls.from_dict(dict_obj)
