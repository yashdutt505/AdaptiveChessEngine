import unittest

import numpy as np

from tools.policy_sensitivity_analysis import choose_configuration, select


class PolicySensitivityTests(unittest.TestCase):
    def test_selection_respects_loss_bound_and_bonus_cap(self):
        scores = np.asarray([100, 90, 64, 60])
        probabilities = np.asarray([.10, .40, .90, 1.0])
        index, bonus = select(scores, probabilities, 100, 20, 4)
        self.assertEqual(index, 1)
        self.assertEqual(bonus, 20)

    def test_configuration_rule_prefers_lift_inside_intervention_range(self):
        configs = [
            {"change_rate": .05, "mean_probability_lift_all_positions": .02, "mean_score_loss_cp": 1,
             "maximum_bonus_cp": 10, "candidate_count": 4, "scale_cp_per_probability": 50},
            {"change_rate": .15, "mean_probability_lift_all_positions": .01, "mean_score_loss_cp": 1,
             "maximum_bonus_cp": 20, "candidate_count": 4, "scale_cp_per_probability": 100},
            {"change_rate": .20, "mean_probability_lift_all_positions": .03, "mean_score_loss_cp": 2,
             "maximum_bonus_cp": 20, "candidate_count": 8, "scale_cp_per_probability": 200},
        ]
        selected, rule = choose_configuration(configs)
        self.assertIs(selected, configs[2])
        self.assertIn("10-25%", rule)


if __name__ == "__main__":
    unittest.main()
