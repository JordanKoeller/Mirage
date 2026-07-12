from dataclasses import dataclass
from typing import List
from copy import copy

from mirage.util import (
  Vec2D,
  PixelRegion,
  DelegateRegistry,
  DictifyMixin,
  Dictify,
)
from mirage.sim import Simulation
from mirage.calc import Reducer, RayTracer

_MACROLENSING_RESOLUTION = Vec2D.unitless(1_200, 1_200)


@DelegateRegistry.register
@dataclass(kw_only=True)
class MacrolensingSimulation(Simulation):
  @classmethod
  def from_dict(cls, sim_dict: dict):
    with Simulation.units_from_dict(sim_dict):
      return Dictify.from_dict(cls, sim_dict, False)

  def to_dict(self) -> dict:
    return Dictify.to_dict(self, allow_custom_serializer=False)

  def get_ray_tracer(self) -> RayTracer:
    return self.lensing_system.get_ray_tracer()

  def get_ray_bundle(self) -> PixelRegion:
    er = self.lensing_system.einstein_radius
    ret = PixelRegion(
      dims=Vec2D(2 * er, 2 * er),
      center=Vec2D.zero_vector(er.unit),
      resolution=copy(_MACROLENSING_RESOLUTION),
    )

    return ret.to("theta_0")

  def get_reducers(self) -> List[Reducer]:  # type: ignore
    return self.reducers
