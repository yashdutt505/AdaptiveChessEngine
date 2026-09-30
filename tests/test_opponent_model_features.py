import unittest

from engine.opponent_model_features import (
    MODEL_FEATURE_NAMES, MODEL_FEATURE_SET_ID, extract_position_features, model_row,
)


class OpponentModelFeatureTests(unittest.TestCase):
    def test_start_position_features_are_symmetric(self):
        features = extract_position_features(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 1164, 1200,
        )
        self.assertEqual(tuple(features), MODEL_FEATURE_NAMES)
        self.assertEqual(features["legal_move_count"], 20)
        self.assertEqual(features["material_balance_cp"], 0)
        self.assertEqual(features["remaining_non_pawn_material_cp"], 6400)
        self.assertEqual(features["remaining_pawn_count"], 16)
        self.assertEqual(features["player_rating"], 1164)
        self.assertEqual(features["rating_difference"], -36)

    def test_balances_use_side_to_move_perspective(self):
        white = extract_position_features("7k/8/8/8/8/8/8/Q6K w - - 0 1", None, None)
        black = extract_position_features("7k/8/8/8/8/8/8/Q6K b - - 0 1", None, None)
        self.assertEqual(white["material_balance_cp"], 900)
        self.assertEqual(black["material_balance_cp"], -900)
        self.assertEqual(white["material_imbalance_cp"], black["material_imbalance_cp"])

    def test_model_row_rejects_excluded_label(self):
        with self.assertRaisesRegex(ValueError, "ineligible"):
            model_row({"label_eligible": False})
        row = model_row({
            "label_eligible": True, "game_id": "g", "ply": 1, "split": "train",
            "fen_before": "7k/8/8/8/8/8/8/Q6K w - - 0 1",
            "player_rating": 1164, "opponent_rating": 1200,
            "large_error": True, "centipawn_loss": 123,
        })
        self.assertEqual(row["feature_set"], MODEL_FEATURE_SET_ID)
        self.assertTrue(row["large_error"])
