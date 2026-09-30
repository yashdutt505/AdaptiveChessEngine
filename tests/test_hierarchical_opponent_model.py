import unittest

import numpy as np

from engine.hierarchical_opponent_model import fit_hierarchical_logistic
from engine.opponent_model_features import MODEL_FEATURE_NAMES, MODEL_FEATURE_SET_ID


def row(value, label):
    features = {name: 0 for name in MODEL_FEATURE_NAMES}
    features["legal_move_count"] = value
    return {"feature_set": MODEL_FEATURE_SET_ID, "features": features, "large_error": label}


class HierarchicalOpponentModelTests(unittest.TestCase):
    def test_requires_both_population_and_personal_data(self):
        with self.assertRaisesRegex(ValueError, "both required"):
            fit_hierarchical_logistic((), (row(1, True),), 0.5)

    def test_personal_predictions_partially_pool_toward_population(self):
        population = tuple(row(value, value > 0) for value in (-2, -1, 1, 2) for _ in range(20))
        personal = tuple(row(value, False) for value in (1, 2) for _ in range(2))
        tight = fit_hierarchical_logistic(population, personal, 0.05)
        loose = fit_hierarchical_logistic(population, personal, 2.0)
        probe = np.asarray([[0 if name != "legal_move_count" else 2 for name in MODEL_FEATURE_NAMES]])
        population_probability = tight.predict_proba(probe, personal=False)[0]
        tight_probability = tight.predict_proba(probe, personal=True)[0]
        loose_probability = loose.predict_proba(probe, personal=True)[0]
        self.assertLess(abs(tight_probability - population_probability), abs(loose_probability - population_probability))


if __name__ == "__main__":
    unittest.main()
