from unittest import TestCase, skip

from astropy import units as u

from mirage.calc import reducers
from mirage.calc.engine import Engine
from mirage.sim import Simulation, MacrolensingSimulation
from mirage.model import Quasar
from mirage.model.impl import PointLens
from mirage.util import PixelRegion, Vec2D


class TestEngine(TestCase):

    def setUp(self):
        self.lens = PointLens(
            quasar=Quasar(redshift=2), redshift=0.5, mass=u.Quantity(1e12, "solMass")
        )

        er = float(self.lens.einstein_radius.to("arcsec").value)

        self.simulation = MacrolensingSimulation(
            lensing_system=self.lens,
            reducers=[
                reducers.LensedImageReducer(
                    query=Vec2D(0, 0, "arcsec"), radius=u.Quantity(0.01, "arcsec")
                )
            ],
            ray_bundle=PixelRegion(
                dims=Vec2D(1, 1, "arcsec"), resolution=Vec2D.unitless(500, 500)
            ),
        )

    @skip("Manual Test")
    def testEndToEnd(self):
        engine = Engine(None, None)
        engine.blocking_run_simulation(self.simulation)
