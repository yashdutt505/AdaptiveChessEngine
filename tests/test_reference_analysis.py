import unittest

from engine.pgn_dataset import DecisionRecord
from engine.reference_analysis import (
    ANALYSIS_VERSION, ReferenceResult, analyze_decision, parse_reference_output,
    validate_resume_prefix,
)


def record(move="e2e4"):
    return DecisionRecord(
        1, "game", "2024.01.01", 0, "train", "Alice", "white", "Bob", 0, 1,
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "e4", move, "1-0", "600", 1500, 1500,
    )


class FakeEngine:
    name = "Fake Reference"
    nodes = 50000

    def __init__(self, best, child):
        self.best = best
        self.child = child

    def analyze(self, _fen, moves=()):
        return self.child if moves else self.best


class ReferenceAnalysisTests(unittest.TestCase):
    def test_uci_output_parser_uses_last_score_and_metadata(self):
        result = parse_reference_output([
            "info depth 5 score cp 12 nodes 100 pv e2e4",
            "info depth 8 score cp 35 nodes 50000 pv e2e4",
            "bestmove e2e4 ponder e7e5",
        ])
        self.assertEqual(result, ReferenceResult(35, None, "e2e4", 8, 50000))

    def test_child_score_is_negated_to_pre_move_player_perspective(self):
        engine = FakeEngine(
            ReferenceResult(80, None, "d2d4", 10, 50000),
            ReferenceResult(20, None, "e7e5", 10, 50000),
        )
        analyzed = analyze_decision(record(), engine)
        self.assertEqual(analyzed.best_score_cp, 80)
        self.assertEqual(analyzed.played_score_cp, -20)
        self.assertEqual(analyzed.centipawn_loss, 100)
        self.assertTrue(analyzed.large_error)
        self.assertTrue(analyzed.label_eligible)

    def test_mate_observation_is_excluded(self):
        engine = FakeEngine(
            ReferenceResult(None, 3, "d1h5", 10, 50000),
            ReferenceResult(0, None, "e7e5", 10, 50000),
        )
        analyzed = analyze_decision(record(), engine)
        self.assertFalse(analyzed.label_eligible)
        self.assertEqual(analyzed.exclusion_reason, "mate-score")

    def test_illegal_dataset_move_fails_before_engine_analysis(self):
        engine = FakeEngine(ReferenceResult(0, None, "e2e4", 1, 1), ReferenceResult(0, None, "e7e5", 1, 1))
        with self.assertRaises(ValueError):
            analyze_decision(record("e2e5"), engine)

    def test_resume_requires_exact_input_prefix_and_node_budget(self):
        decision = record()
        row = analyzed_row = analyze_decision(
            decision,
            FakeEngine(
                ReferenceResult(10, None, "e2e4", 1, 50000),
                ReferenceResult(-10, None, "e7e5", 1, 50000),
            ),
        ).to_dict()
        self.assertEqual(row["analysis_version"], ANALYSIS_VERSION)
        validate_resume_prefix((decision,), (analyzed_row,), 50000)
        with self.assertRaisesRegex(ValueError, "node budget"):
            validate_resume_prefix((decision,), (analyzed_row,), 10000)
        changed = dict(analyzed_row, played_uci="d2d4")
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_resume_prefix((decision,), (changed,), 50000)


if __name__ == "__main__":
    unittest.main()
