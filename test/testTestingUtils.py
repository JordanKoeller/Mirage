

from . import MirageTestCase

class TestMirageTestCase(MirageTestCase):

    def testCanInstantiateSimulation(self):
        sim = self.microlensing_simulation
        self.assertTrue(True)