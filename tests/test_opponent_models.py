import unittest

import numpy as np

from engine.opponent_model_features import MODEL_FEATURE_NAMES, MODEL_FEATURE_SET_ID
from engine.opponent_models import expected_calibration_error, matrix, probability_metrics


class OpponentModelTests(unittest.TestCase):
    def test_matrix_uses_declared_feature_order(self):
        features = {name: index for index, name in enumerate(reversed(MODEL_FEATURE_NAMES))}
        row = {"feature_set": MODEL_FEATURE_SET_ID, "features": features, "large_error": True}
        values, labels = matrix((row,))
        self.assertEqual(values.shape, (1, len(MODEL_FEATURE_NAMES)))
        self.assertEqual(values[0, 0], features[MODEL_FEATURE_NAMES[0]])
        self.assertEqual(labels.tolist(), [1])

    def test_probability_metrics_reward_correct_predictions(self):
        labels = np.asarray([0, 0, 1, 1])
        good = probability_metrics(labels, np.asarray([0.1, 0.2, 0.8, 0.9]))
        weak = probability_metrics(labels, np.full(4, 0.5))
        self.assertLess(good["log_loss"], weak["log_loss"])
        self.assertLess(good["brier_score"], weak["brier_score"])
        self.assertEqual(good["roc_auc"], 1.0)

    def test_calibration_error_is_zero_for_matching_bins(self):
        labels = np.asarray([0, 0, 1, 1])
        probabilities = np.asarray([0.0, 0.0, 1.0, 1.0])
        self.assertEqual(expected_calibration_error(labels, probabilities), 0.0)


if __name__ == "__main__":
    unittest.main()
