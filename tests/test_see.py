import unittest

from engine.movegen import generate_legal_moves
from engine.move import move_to_string
from engine.see import static_exchange_eval
from tests.helpers import position_from_fen


def find_move(position, text):
    return next(move for move in generate_legal_moves(position) if move_to_string(move) == text)


class StaticExchangeTests(unittest.TestCase):
    def test_winning_capture_is_positive(self):
        position = position_from_fen("q6k/8/8/8/8/8/8/R5K1 w - - 0 1")
        self.assertGreater(static_exchange_eval(position, find_move(position, "a1a8")), 0)

    def test_poisoned_pawn_capture_is_negative(self):
        position = position_from_fen("6k1/8/8/4p3/3p4/8/8/3Q2K1 w - - 0 1")
        self.assertLess(static_exchange_eval(position, find_move(position, "d1d4")), 0)

    def test_even_pawn_trade_is_neutral(self):
        position = position_from_fen("6k1/8/4p3/3p4/2P5/8/8/6K1 w - - 0 1")
        self.assertEqual(static_exchange_eval(position, find_move(position, "c4d5")), 0)
