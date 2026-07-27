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
