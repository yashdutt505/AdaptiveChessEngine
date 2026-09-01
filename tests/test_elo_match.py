import unittest

from tools.elo_match import estimate_elo, parse_uci_options


class EloMatchTests(unittest.TestCase):
    def test_even_score_matches_opponent_rating(self):
        score, estimate, interval = estimate_elo(1800, [1.0, 0.0, 0.5, 0.5])
        self.assertEqual(score, 0.5)
        self.assertAlmostEqual(estimate, 1800)
        self.assertLess(interval[0], estimate)
        self.assertGreater(interval[1], estimate)

    def test_perfect_score_is_reported_without_false_precision(self):
        score, estimate, interval = estimate_elo(1800, [1.0, 1.0])
        self.assertEqual(score, 1.0)
        self.assertIsNone(estimate)
        self.assertIsNone(interval)

    def test_target_options_support_compute_matched_experiments(self):
        self.assertEqual(
            parse_uci_options(["MultiPV=4", "Adaptive Mode=false"]),
            [("MultiPV", "4"), ("Adaptive Mode", "false")],
        )
        with self.assertRaises(ValueError):
            parse_uci_options(["Adaptive Mode"])
        with self.assertRaises(ValueError):
            parse_uci_options(["=true"])


if __name__ == "__main__":
    unittest.main()
