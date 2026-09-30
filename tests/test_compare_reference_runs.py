import unittest

from tools.compare_reference_runs import compare


def row(game, ply, label, loss, eligible=True):
    return {
        "game_id": game, "ply": ply, "large_error": label,
        "centipawn_loss": loss, "label_eligible": eligible,
    }


class ReferenceComparisonTests(unittest.TestCase):
    def test_reports_agreement_kappa_and_loss_differences(self):
        left = (row("a", 1, False, 20), row("b", 2, True, 120), row("c", 3, True, 150))
        right = (row("a", 1, False, 30), row("b", 2, True, 110), row("c", 3, False, 80))
        result = compare(left, right)
        self.assertEqual(result["label_flips"], 1)
        self.assertAlmostEqual(result["binary_agreement"], 2 / 3)
        self.assertEqual(result["median_absolute_cpl_difference"], 10)

    def test_rejects_different_decision_sets(self):
        with self.assertRaisesRegex(ValueError, "same decisions"):
            compare((row("a", 1, False, 0),), (row("b", 1, False, 0),))


if __name__ == "__main__":
    unittest.main()
