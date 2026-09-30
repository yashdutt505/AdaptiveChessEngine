import unittest

from engine.chesscom_archive import summarize_games


class ChessComArchiveTests(unittest.TestCase):
    def test_summary_counts_deduplication_and_cohorts(self):
        games = [
            {"uuid": "a", "rules": "chess", "time_class": "rapid", "time_control": "600", "pgn": "one"},
            {"uuid": "b", "rules": "chess", "time_class": "blitz", "time_control": "180", "pgn": "two"},
            {"uuid": "a", "rules": "chess", "time_class": "rapid", "time_control": "600", "pgn": "one"},
        ]
        summary = summarize_games("YashDutt7", ["2024/01", "2024/02"], games, "one\ntwo\n")
        self.assertEqual(summary.downloaded_games, 3)
        self.assertEqual(summary.unique_games, 2)
        self.assertEqual(summary.duplicate_games, 1)
        self.assertEqual(summary.by_time_class, {"blitz": 1, "rapid": 2})
        self.assertEqual(summary.by_time_control["600"], 2)
        self.assertEqual(len(summary.combined_pgn_sha256), 64)


if __name__ == "__main__":
    unittest.main()
