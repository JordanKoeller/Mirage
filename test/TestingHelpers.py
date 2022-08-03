import os
from unittest import TestCase

import numpy as np
from numpy import testing as np_test

MICROLENSING_SIMULATION_FIXTURE_FILE = os.path.join(os.getcwd(), 'test','fixtures','microlensing_parameters.sim')
SCALE_SIMULATION_FIXTURE_FILE = os.path.join(os.getcwd(), 'test','fixtures','scale_test_parameters.sim')
MACROLENSING_SIMULATION_FIXTURE_FILE = os.path.join(os.getcwd(), 'test','fixtures','macrolensing_parameters.sim')


class MirageTestCase(TestCase):

    _scale_sim = None

    def assertAlmostEqual(self, first, second, tol=1e-10):
        if isinstance(first, float) or isinstance(second, float):
            return TestCase.assertAlmostEqual(self, first, second)
        else:
            if first.shape != second.shape:
                raise AssertionError(f"Arrays had different shapes of A={first.shape} and B={second.shape}, respectively")
            first = first.flatten()
            second = second.flatten()
            mismatch_count = 0
            max_diff = 0
            for i in range(len(first)):
                abs_diff = abs(first[i] - second[i])
                if abs_diff >= tol:
                    mismatch_count += 1
                    max_diff = max(max_diff, abs_diff)
                    # print("Had diff", first[i], second[i])
            if mismatch_count > 0:
                raise AssertionError(f"""
Arrays had a mismatch of {mismatch_count} / {len(first)} ({mismatch_count / len(first) * 100}%)
Max Difference={max_diff}
A={first}
B={second}""")

    def assertNotAlmostEqual(self, first, second, tol=1e-10):
        try:
            self.assertAlmostEqual(first, second, tol)
        except AssertionError:
            return
        raise AssertionError()

    def assertAlmostSetEqual(self, first, second, tol=1e-10):
        first = np.array(first)
        second = np.array(second)
        first = first.flatten()
        second = second.flatten()
        self.assertEqual(first.shape, second.shape)
        first = np.sort(first)
        second = np.sort(second)
        for a, b in zip(first, second):
            if abs(a - b) >= tol:
                raise AssertionError("Arrays were not approximately set-equal")

    @property
    def microlensing_simulation(self):
        from mirage.util.io import SimulationFileManager
        # from mirage.io import SimulationFileManager
        manager = SimulationFileManager()
        manager.open(MICROLENSING_SIMULATION_FIXTURE_FILE)
        ret = manager.read()
        manager.close()
        return ret

    @property
    def scale_simulation(self):
        if self._scale_sim:
            return self._scale_sim
        from mirage.util.io import SimulationFileManager
        manager = SimulationFileManager()
        manager.open(SCALE_SIMULATION_FIXTURE_FILE)
        self._scale_sim = manager.read()
        manager.close()
        return self._scale_sim

    @property
    def fixture_paths(self):
        return [
            MICROLENSING_SIMULATION_FIXTURE_FILE,
            MACROLENSING_SIMULATION_FIXTURE_FILE,
        ]
