import unittest

from engine.benchmark import run_tactical_benchmark


class TacticalBenchmarkTests(unittest.TestCase):
    def test_tactical_suite(self):
        results = run_tactical_benchmark(depth=2)
        failures = [result for result in results if not result["passed"]]
        self.assertEqual(failures, [])
