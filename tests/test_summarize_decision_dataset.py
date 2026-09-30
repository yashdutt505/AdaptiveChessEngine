import unittest

from engine.pgn_dataset import DecisionRecord
from tools.summarize_decision_dataset import summarize


def record(game, split, color, result, rating, opponent_rating, ply):
    return DecisionRecord(
        1, game, "2024.01.01", 0, split, "Alice", color, "Bob", ply, 1,
        "8/8/8/8/8/8/8/8 w - - 0 1", "", "", result, "600", rating, opponent_rating,
    )


class DatasetSummaryTests(unittest.TestCase):
    def test_summarizes_games_without_counting_each_decision_as_a_game(self):
        records = (
            record("a", "train", "white", "1-0", 1000, 1100, 0),
            record("a", "train", "white", "1-0", 1000, 1100, 2),
            record("b", "train", "black", "1-0", 1200, 1100, 1),
        )
        result = summarize(records)
        self.assertEqual(result["games"], 2)
        self.assertEqual(result["decisions"], 3)
        self.assertEqual(result["outcomes"], {"loss": 1, "win": 1})
        self.assertEqual(result["player_rating"]["mean"], 1100)


if __name__ == "__main__":
    unittest.main()
