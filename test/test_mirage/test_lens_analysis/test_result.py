import pytest

import numpy as np

from matplotlib import pyplot as plt

from mirage.lens_analysis import ExperimentResult, SimulationResult
from mirage.io import ResultFileManager
from mirage.util import VariantKey


@pytest.fixture
def experiment_result() -> ExperimentResult:
  """
  Opens the test fixture microlensing_result in read-only mode.
  """
  fm = ResultFileManager("test/testdata/microlensing_result.zip", "r")
  return ExperimentResult(fm)


@pytest.fixture
def simulation_result(
  experiment_result: ExperimentResult, radius: int = 0
) -> SimulationResult:
  """
  Opens the test fixture microlensing_result in read-only mode.
  """
  return experiment_result.simulation(VariantKey(radius=radius))


class TestExperimentResult:
  def testLoad(self, experiment_result: ExperimentResult) -> None:
    assert len(experiment_result) == 8
    assert experiment_result.keys == [
      VariantKey(radius=0),
      VariantKey(radius=1),
      VariantKey(radius=2),
      VariantKey(radius=3),
      VariantKey(radius=4),
      VariantKey(radius=5),
      VariantKey(radius=6),
      VariantKey(radius=7),
    ]

  def testGetByVariantKey(self, experiment_result: ExperimentResult) -> None:
    simulation_result_0 = experiment_result.simulation(VariantKey(radius=0))
    simulation_result_4 = experiment_result.simulation(VariantKey(radius=4))
    assert simulation_result_0.variant_key == VariantKey(radius=0)
    assert simulation_result_4.variant_key == VariantKey(radius=4)

  def testCanForLoop(self, experiment_result: ExperimentResult):
    expected_keys = [
      VariantKey(radius=0),
      VariantKey(radius=1),
      VariantKey(radius=2),
      VariantKey(radius=3),
      VariantKey(radius=4),
      VariantKey(radius=5),
      VariantKey(radius=6),
      VariantKey(radius=7),
    ]
    for expected_key, simulation_result in zip(expected_keys, experiment_result):
      assert expected_key == simulation_result.variant_key

  @pytest.mark.skip("Integration test.")
  def testShowMaps(self, experiment_result: ExperimentResult) -> None:
    for sim in experiment_result:
      reducer = sim.get_reducer("magmap").output
      plt.imshow(reducer)
      plt.show()


class TestSimulationResultResult:
  def testLoad(self, simulation_result: SimulationResult) -> None:
    assert len(simulation_result) == 2
    assert simulation_result.reducer_names == ["magmap", "lightcurves"]

  def testGetReducer(self, simulation_result: SimulationResult) -> None:
    magmap = simulation_result.get_reducer("magmap").output
    assert magmap.shape == (512, 512)
    assert np.sum(magmap) > 0
