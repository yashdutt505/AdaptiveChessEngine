import unittest

from engine.evaluation import evaluate
from tests.helpers import position_from_fen


class EvaluationTests(unittest.TestCase):
    def test_material_advantage_is_positive_for_side_to_move(self):
        white = position_from_fen("7k/8/8/8/8/8/8/Q5K1 w - - 0 1")
        black = position_from_fen("q5k1/8/8/8/8/8/8/7K b - - 0 1")
        self.assertGreater(evaluate(white), 800)
        self.assertGreater(evaluate(black), 800)

    def test_side_to_move_changes_score_perspective(self):
        white = position_from_fen("7k/8/8/8/8/8/8/Q5K1 w - - 0 1")
        black = position_from_fen("7k/8/8/8/8/8/8/Q5K1 b - - 0 1")
        self.assertEqual(evaluate(white), -evaluate(black))

    def test_castled_king_with_pawn_shield_is_safer(self):
        safe = position_from_fen("r2q2k1/5ppp/8/8/8/8/5PPP/R2Q2K1 w - - 0 1")
        exposed = position_from_fen("r2q2k1/5ppp/8/8/8/8/5PPP/R2KQ3 w - - 0 1")
        self.assertGreater(evaluate(safe), evaluate(exposed))

    def test_advanced_passed_pawn_is_more_valuable(self):
        advanced = position_from_fen("7k/4P3/8/8/8/8/8/7K w - - 0 1")
        starting = position_from_fen("7k/8/8/8/8/8/4P3/7K w - - 0 1")
        self.assertGreater(evaluate(advanced), evaluate(starting))

    def test_rook_prefers_open_file(self):
        open_file = position_from_fen("7k/p7/8/8/8/8/1P6/R6K w - - 0 1")
        blocked = position_from_fen("7k/p7/8/8/8/8/P7/R6K w - - 0 1")
        self.assertGreater(evaluate(open_file), evaluate(blocked))
