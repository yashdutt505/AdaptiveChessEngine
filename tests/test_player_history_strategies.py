import unittest

import numpy as np

from tools.compare_player_history_strategies import games_in_order, latest_games, recency_weights


class PlayerHistoryStrategyTests(unittest.TestCase):
    def setUp(self):
        self.rows = tuple(
            {"game_id": game, "row": row}
            for game in ("a", "b", "c")
            for row in range(2)
        )

    def test_latest_games_keeps_whole_games_and_source_order(self):
        selected = latest_games(self.rows, 2)
        self.assertEqual(games_in_order(selected), ("b", "c"))
        self.assertEqual([row["row"] for row in selected], [0, 1, 0, 1])

    def test_recency_weights_are_equal_within_game_and_halve(self):
        weights = recency_weights(self.rows, 1)
        np.testing.assert_allclose(weights, [0.25, 0.25, 0.5, 0.5, 1.0, 1.0])

    def test_half_life_must_be_positive(self):
        with self.assertRaises(ValueError):
            recency_weights(self.rows, 0)


if __name__ == "__main__":
    unittest.main()
