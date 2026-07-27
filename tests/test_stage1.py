import unittest

from engine.constants import START_FEN
from engine.fen import load_fen, position_to_fen, verify_round_trip
from engine.position import Position
from engine.validator import validate_position
from engine.zobrist import compute_hash
from tests.helpers import legal_move, position_from_fen


class FenTests(unittest.TestCase):
    def test_start_position_round_trip(self):
        self.assertTrue(verify_round_trip(START_FEN))

    def test_complex_position_round_trip(self):
        fen = "r3k2r/ppp2ppp/2n5/3pp3/3PP3/2N5/PPP2PPP/R3K2R b KQkq e3 4 12"
        self.assertTrue(verify_round_trip(fen))

    def test_fen_requires_six_fields(self):
        with self.assertRaises(ValueError):
            load_fen(Position(), "8/8/8/8/8/8/8/8 w - -")


class MakeUnmakeTests(unittest.TestCase):
    CASES = (
        (START_FEN, "e2e4"),
        ("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5"),
        ("8/P7/8/8/8/8/8/k6K w - - 0 1", "a7a8q"),
        ("4k2r/8/8/8/8/8/8/4K2R w Kk - 0 1", "e1g1"),
        ("r3k3/8/8/8/8/8/8/R3K3 w Qq - 0 1", "e1c1"),
        ("8/8/8/3pP3/8/8/8/k6K w - d6 0 1", "e5d6"),
    )

    def test_every_special_move_restores_exact_position(self):
        for fen, uci in self.CASES:
            with self.subTest(move=uci):
                position = position_from_fen(fen)
                original_fen = position_to_fen(position)
                original_hash = position.hash_key
                move = legal_move(position, uci)

                position.make_move(move)
                self.assertEqual(len(position.history), 1)
                validate_position(position)
                self.assertEqual(position.hash_key, compute_hash(position))

                position.unmake_move()
                self.assertEqual(len(position.history), 0)
                self.assertEqual(position_to_fen(position), original_fen)
                self.assertEqual(position.hash_key, original_hash)
                validate_position(position)

    def test_long_sequence_unmakes_to_start(self):
        position = position_from_fen(START_FEN)
        original_hash = position.hash_key
        played = []
        for uci in ("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"):
            move = legal_move(position, uci)
            position.make_move(move)
            played.append(move)
            validate_position(position)

        self.assertEqual(len(position.history), len(played))
        for _ in played:
            position.unmake_move()

        self.assertEqual(position_to_fen(position), START_FEN)
        self.assertEqual(position.hash_key, original_hash)
        self.assertEqual(len(position.history), 0)
