import unittest

from engine.constants import START_FEN
from engine.fen import position_to_fen
from engine.perft import perft
from tests.helpers import position_from_fen


class PerftTests(unittest.TestCase):
    CASES = (
        ("Start position", START_FEN, {1: 20, 2: 400, 3: 8902, 4: 197281}),
        (
            "Kiwipete",
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
            {1: 48, 2: 2039, 3: 97862},
        ),
        (
            "Position 3",
            "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
            {1: 14, 2: 191, 3: 2812, 4: 43238},
        ),
    )

    def test_reference_node_counts(self):
        for name, fen, expected_by_depth in self.CASES:
            for depth, expected in expected_by_depth.items():
                with self.subTest(position=name, depth=depth):
                    position = position_from_fen(fen)
                    original_fen = position_to_fen(position)
                    original_hash = position.hash_key
                    self.assertEqual(perft(position, depth), expected)
                    self.assertEqual(position_to_fen(position), original_fen)
                    self.assertEqual(position.hash_key, original_hash)
                    self.assertEqual(len(position.history), 0)
