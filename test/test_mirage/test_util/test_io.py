from pathlib import Path

from pytest import fixture
import pytest
from astropy.units import Quantity
from astropy import units as u

from mirage.sim import MicrolensingSimulation, Simulation, Experiment
from mirage.model import Quasar, Starfield
from mirage.model.initial_mass_function import WeidnerKroupa2004
from mirage.model.impl import PointLens
from mirage.util import Vec2D, VariantKey
from mirage.io import ResultFileManager
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
def experiment() -> Experiment:
    return Experiment.from_single_variant(simulation())


@fixture
def light_curve_reducer(radius: int = 1) -> LightCurvesReducer:
    return LightCurvesReducer(
        radius=radius * u.arcsec,
        resolution=10 / u.arcsec,
        num_curves=5,
        seed=12,
        name="lightcurve",
    )


def reducer(radius: int = 1) -> LightCurvesReducer:
    return LightCurvesReducer(
        radius=radius * u.arcsec,
        resolution=10 / u.arcsec,
        num_curves=5,
        seed=12,
        name=f"lightcurve{radius}",
    )


class TestResultFileManager:
    def test_dumpExperiment_success(self, tmp_path: Path, experiment: Experiment):
        file_path = tmp_path / "some-file.zip"
        mgr = ResultFileManager.new_writer(str(file_path))
        mgr.dump_experiment(experiment)  # type: ignore
        mgr.close()  # type: ignore

    def test_loadExperiment_success(self, tmp_path: Path, experiment: Experiment):
        file_path = tmp_path / "some-file.zip"
        mgr = ResultFileManager.new_writer(str(file_path))
        mgr.dump_experiment(experiment=experiment)  # type: ignore
        mgr.close()  # type: ignore

        mgr = ResultFileManager.new_loader(str(file_path))
        sim_batch = mgr.load_experiment()  # type: ignore
        mgr.close()  # type: ignore

        assert sim_batch == experiment

    def test_dumpResult_success(
        self, tmp_path: Path, light_curve_reducer: LightCurvesReducer
    ):
        file_path = tmp_path / "some-file.zip"
        experiment = Experiment.from_single_variant(
            simulation(100000, [light_curve_reducer])
        )
        mgr = ResultFileManager.new_writer(str(file_path))
        mgr.dump_experiment(experiment=experiment)  # type: ignore
        mgr.dump_result(light_curve_reducer, VariantKey({}))
        mgr.close()

        mgr = ResultFileManager.new_loader(str(file_path))
        reducer = mgr.load_result(light_curve_reducer.name, VariantKey({}))
        mgr.close()  # type: ignore

        assert reducer == light_curve_reducer
