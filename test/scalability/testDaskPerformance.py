
from ..TestingHelpers import MirageTestCase

from mirage.engine import DaskCalculationDelegate
from mirage.util import Vec2D, StopWatch

class TestDaskPerformance(MirageTestCase):

    def setUp(self):
        self.calculator = DaskCalculationDelegate()
        if not hasattr(self, 'stopwatch'):
            self.stopwatch = StopWatch()
        self.stopwatch.refresh()
        

    def setScaleParameters(self, region_edge: int, starry_pcnt: int):
        self.scale_simulation._parameters._percent_stars = starry_pcnt / 100
        self.scale_simulation._parameters._ray_region._resolution = Vec2D(region_edge, region_edge)

    @property
    def ops(self):
        return self.scale_simulation.parameters.stars.shape[0] * self.scale_simulation._parameters._ray_region.resolution.x**2

    @property
    def tenBilOps(self):
        return self.scale_simulation.parameters.stars.shape[0] * 1e10

    def testDaskRayTracerPerformance(self):
        self.setScaleParameters(5000, 100)
        self.stopwatch.start()
        self.calculator.reconfigure(self.scale_simulation._parameters)
        print("Num partitions", self.calculator.array.npartitions)
        self.calculator.array.compute(scheduler='threads')
        self.stopwatch.stop()
        gOps = self.ops / 1e9
        secs = self.stopwatch.secs
        longRunTiming = self.tenBilOps / (self.ops / secs)
        hours = longRunTiming / 3600
        print(f"Had {gOps / secs} GOps / sec. Predict {hours} hours for 10B Rays tracing.")