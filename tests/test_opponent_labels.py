import unittest

from engine.opponent_labels import LABEL_VERSION, label_decision


class OpponentLabelTests(unittest.TestCase):
    def test_large_error_boundary_is_inclusive(self):
        below = label_decision(35, -64)
        boundary = label_decision(35, -65)
        self.assertEqual(below.centipawn_loss, 99)
        self.assertFalse(below.large_error)
        self.assertEqual(boundary.centipawn_loss, 100)
        self.assertTrue(boundary.large_error)
        self.assertEqual(boundary.version, LABEL_VERSION)

    def test_better_than_reference_is_zero_loss(self):
        label = label_decision(20, 25)
        self.assertEqual(label.centipawn_loss, 0)
        self.assertFalse(label.large_error)

    def test_custom_threshold_is_recorded(self):
        label = label_decision(80, 30, threshold_cp=50)
        self.assertEqual(label.threshold_cp, 50)
        self.assertTrue(label.large_error)

    def test_mate_scores_are_excluded_from_v1(self):
        label = label_decision(1000, 0, best_is_mate=True)
        self.assertFalse(label.eligible)
        self.assertIsNone(label.centipawn_loss)
        self.assertIsNone(label.large_error)
        self.assertEqual(label.exclusion_reason, "mate-score")

    def test_invalid_numeric_inputs_are_rejected(self):
        for args in ((True, 0), (0, 1.5)):
            with self.assertRaises(ValueError):
                label_decision(*args)
        with self.assertRaises(ValueError):
            label_decision(0, 0, threshold_cp=0)


if __name__ == "__main__":
    unittest.main()
