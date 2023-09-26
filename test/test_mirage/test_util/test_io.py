from pathlib import Path

from pytest import fixture
from astropy.units import Quantity
from astropy import units as u
import numpy as np

from mirage.sim import MicrolensingSimulation, Simulation, SimulationBatch
from mirage.model import Quasar, Starfield
from mirage.model.initial_mass_function import WeidnerKroupa2004
from mirage.model.impl import PointLens
from mirage.util import Vec2D, Dictify, ResultFileManager
from mirage.calc.reducers import LightCurvesReducer


def simulation(ray_count: int = 100_000, reducers=None) -> Simulation:
  return MicrolensingSimulation(
    lensing_system=PointLens(
      quasar=Quasar(2.0, mass=Quantity(1e9, "solMass")),
      redshift=0.5,
      mass=Quantity(1e12, "solMass"),
    ),
    lensed_image_center=Vec2D(0.2, 2.1, "arcsec"),
    ray_count=ray_count,
    source_region_dimensions=Vec2D(1.2, 1.2, "arcsec"),
    starfield=Starfield(initial_mass_function=WeidnerKroupa2004(), seed=2),
    reducers=reducers if reducers else [],
  )


@fixture
def simulation_batch() -> SimulationBatch:
  return SimulationBatch([simulation()])


@fixture
def light_curve_reducer(radius: int = 1) -> LightCurvesReducer:
  return LightCurvesReducer(
    radius=radius * u.arcsec,
    resolution=10 / u.arcsec,
    num_curves=5,
    seed=12,
    name="lightcurve")


def reducer(radius: int = 1) -> LightCurvesReducer:
  return LightCurvesReducer(
    radius=radius * u.arcsec,
    resolution=10 / u.arcsec,
    num_curves=5,
    seed=12,
    name=f"lightcurve{radius}")


class TestResultFileManager:

  def test_dumpSimulation_success(self, tmp_path: Path, simulation_batch: SimulationBatch):
    file_path = tmp_path / "some-file.zip"
    mgr = ResultFileManager.new_writer(str(file_path))
    mgr.dump_simulation(simulation_batch=simulation_batch)  # type: ignore
    mgr.close()  # type: ignore

  def test_loadSimulation_success(self, tmp_path: Path, simulation_batch: SimulationBatch):
    file_path = tmp_path / "some-file.zip"
    mgr = ResultFileManager.new_writer(str(file_path))
    mgr.dump_simulation(simulation_batch=simulation_batch)  # type: ignore
    mgr.close()  # type: ignore

    mgr = ResultFileManager.new_loader(str(file_path))
    sim_batch = mgr.load_simulation()  # type: ignore
    mgr.close()  # type: ignore

    assert sim_batch == simulation_batch

  def test_dumpResult_success(self, tmp_path: Path, light_curve_reducer: LightCurvesReducer):
    file_path = tmp_path / "some-file.zip"
    simulation_batch = SimulationBatch([simulation(100000, [light_curve_reducer])])
    mgr = ResultFileManager.new_writer(str(file_path))
    mgr.dump_simulation(simulation_batch=simulation_batch)  # type: ignore
    mgr.dump_result(light_curve_reducer, 0)
    mgr.close()

    mgr = ResultFileManager.new_loader(str(file_path))
    reducer = mgr.load_result(light_curve_reducer.name, 0)
    mgr.close()  # type: ignore

    assert mgr.manifest[0][light_curve_reducer.name] == f"{light_curve_reducer.name}_0.pickle"
    assert reducer == light_curve_reducer

  def test_dumpResult_multipleResultsAndMultipleSims_success(self, tmp_path: Path):
    file_path = tmp_path / "some-file.zip"

    reducers = [reducer(i) for i in range(9)]

    sims = [
      simulation(10_000, reducers),
      simulation(100_000, reducers),
      simulation(1_000_000, reducers),
    ]

    mgr = ResultFileManager.new_writer(str(file_path))
    mgr.dump_simulation(SimulationBatch(sims))

    mgr.dump_result(reducers[0], 0)
    mgr.dump_result(reducers[1], 0)
    mgr.dump_result(reducers[2], 0)
    mgr.dump_result(reducers[3], 1)
    mgr.dump_result(reducers[4], 1)
    mgr.dump_result(reducers[5], 1)
    mgr.dump_result(reducers[6], 2)
    mgr.dump_result(reducers[7], 2)
    mgr.dump_result(reducers[8], 2)
    mgr.close()

    mgr = ResultFileManager.new_loader(str(file_path))
    sim = mgr.load_simulation()

    assert sim == SimulationBatch(sims)
    assert mgr.load_result(reducers[0].name, 0) == reducers[0]
    assert mgr.load_result(reducers[1].name, 0) == reducers[1]
    assert mgr.load_result(reducers[2].name, 0) == reducers[2]
    assert mgr.load_result(reducers[3].name, 1) == reducers[3]
    assert mgr.load_result(reducers[4].name, 1) == reducers[4]
    assert mgr.load_result(reducers[5].name, 1) == reducers[5]
    assert mgr.load_result(reducers[6].name, 2) == reducers[6]
    assert mgr.load_result(reducers[7].name, 2) == reducers[7]
    assert mgr.load_result(reducers[8].name, 2) == reducers[8]
