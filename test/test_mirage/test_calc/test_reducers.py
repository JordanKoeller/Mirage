from unittest import TestCase
import pytest

from matplotlib import pyplot as plt
from astropy import units as u
import numpy as np

from mirage.calc.reducers import LightCurvesReducer, MagnificationMapReducer
from mirage.lens_analysis import ExperimentResult, SimulationResult
from mirage.util import Region, Vec2D, Index2D, VariantKey
from mirage.io import ResultFileManager


class TestLightCurvesReducer(TestCase):
    def setUp(self):
        plt.cla()
        self.lcr = LightCurvesReducer(
            radius=1 * u.arcsec,
            resolution=10 / u.arcsec,
            num_curves=5,
            seed=12,
            name="lightcurve",
        )
        self.region = Region(
            dims=Vec2D(10, 10, u.arcsec), center=Vec2D(1.2, -4.0, u.arcsec)
        )
        fm = ResultFileManager("test/testdata/microlensing_result.zip", "r")
        experiment = ExperimentResult(fm)
        simulation = experiment.simulation(VariantKey(radius=0))
        self.magmap = simulation.get_reducer("magmap")

    def testGetQuerySeeds_success(self):
        seeds = self.lcr.get_query_seeds(self.region)
        self.assertEqual(seeds.shape[0], self.lcr.num_curves)
        self.assertEqual(seeds.unit, u.arcsec)
        lows, highs = self.region.span
        for i in range(self.lcr.num_curves):
            x0, y0, x1, y1 = seeds[i].value
            self.assertAlmostWithin(x0, lows.x.value, highs.x.value)
            self.assertAlmostWithin(x1, lows.x.value, highs.x.value)
            self.assertAlmostWithin(y0, lows.y.value, highs.y.value)
            self.assertAlmostWithin(y1, lows.y.value, highs.y.value)

    def testGetQueryPoints_interpolatesWithSpecifiedResolution(self):
        lines = self.lcr.get_query_points(self.region)
        for line in lines:
            line = line.value
            dx = line[1, 0] - line[0, 0]
            dy = line[1, 1] - line[0, 1]
            r = np.sqrt(dx**2 + dy**2)
            self.assertAlmostEqual(r, 0.1)

    def testSlicePositiveSlopeOnDiagonal(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 10), Index2D(90, 90))
        self.assertEqual(len(data), 81)

    def testSlicePositiveSlopeOffDiagnol(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 9), Index2D(90, 91))
        self.assertEqual(len(data), 160)

    def testSliceSteepSlope(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 10), Index2D(50, 90))
        self.assertEqual(len(data), 80)

    def testSliceLowSlope(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 10), Index2D(90, 50))
        self.assertEqual(len(data), 81)

    def testSliceNegativeSlope(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 90), Index2D(90, 50))
        self.assertEqual(len(data), 81)

    def testSliceRightToLeft(self) -> None:
        x, data = self.magmap.slice(Index2D(90, 90), Index2D(10, 50))
        self.assertEqual(len(data), 81)

    def testSliceHorizontalLine(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 10), Index2D(90, 10))
        self.assertEqual(len(data), 81)

    def testSliceVerticalLine(self) -> None:
        x, data = self.magmap.slice(Index2D(10, 10), Index2D(10, 90))
        self.assertEqual(len(data), 81)

    def assertAlmostWithin(self, v, low, high, tol=1e-8):
        self.assertGreaterEqual(v, low - tol)
        self.assertLessEqual(v, high + tol)
