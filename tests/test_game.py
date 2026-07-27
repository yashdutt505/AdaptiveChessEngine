import unittest

from engine.constants import START_FEN
from engine.game import (
    is_fifty_move_draw,
    is_insufficient_material,
    is_threefold_repetition,
)
from tests.helpers import legal_move, position_from_fen


class DrawTests(unittest.TestCase):
    def test_fifty_move_rule(self):
        position = position_from_fen("7k/8/8/8/8/8/8/R5K1 w - - 100 51")
        self.assertTrue(is_fifty_move_draw(position))

    def test_insufficient_material(self):
        for fen in (
            "7k/8/8/8/8/8/8/6K1 w - - 0 1",
            "7k/8/8/8/8/8/8/2B3K1 w - - 0 1",
            "5b1k/8/8/8/8/8/8/2B3K1 w - - 0 1",
        ):
            with self.subTest(fen=fen):
                self.assertTrue(is_insufficient_material(position_from_fen(fen)))

    def test_threefold_repetition_from_history(self):
        position = position_from_fen(START_FEN)
        for _ in range(2):
            for uci in ("g1f3", "g8f6", "f3g1", "f6g8"):
                position.make_move(legal_move(position, uci))
        self.assertTrue(is_threefold_repetition(position))
