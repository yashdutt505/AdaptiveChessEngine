import unittest

from engine.benchmark import run_performance_benchmark, run_tactical_benchmark


class TacticalBenchmarkTests(unittest.TestCase):
    def test_tactical_suite(self):
        results = run_tactical_benchmark(depth=2)
        failures = [result for result in results if not result["passed"]]
        self.assertEqual(failures, [])

    def test_performance_baseline_reports_correct_perft(self):
        result = run_performance_benchmark(perft_depth=2, search_depth=1)
        self.assertEqual(result["perft_nodes"], 400)
        self.assertGreater(result["perft_nps"], 0)
        self.assertIsInstance(result["best_move"], str)
