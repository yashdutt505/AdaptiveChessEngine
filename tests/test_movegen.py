import random
import unittest

from engine.attacks import is_in_check, is_square_attacked
from engine.constants import BLACK, START_FEN, WHITE
from engine.move import move_to_string
from engine.movegen import generate_legal_moves, generate_legal_moves_reference
from engine.squares import square_from_string
from tests.helpers import position_from_fen


class AttackTests(unittest.TestCase):
    def test_sliding_and_knight_attacks(self):
        position = position_from_fen("4k3/8/2n5/8/4B3/8/8/4K3 w - - 0 1")
        self.assertTrue(is_square_attacked(position, square_from_string("d4"), BLACK))
        self.assertTrue(is_square_attacked(position, square_from_string("d5"), WHITE))

    def test_check_detection(self):
        position = position_from_fen("4k3/8/8/8/8/8/4r3/4K3 w - - 0 1")
        self.assertTrue(is_in_check(position, WHITE))
        self.assertFalse(is_in_check(position, BLACK))


class LegalMoveTests(unittest.TestCase):
    def move_strings(self, fen):
        return {move_to_string(move) for move in generate_legal_moves(position_from_fen(fen))}

    def test_start_position_has_twenty_moves(self):
        self.assertEqual(len(self.move_strings(START_FEN)), 20)

    def test_pinned_piece_cannot_expose_king(self):
        moves = self.move_strings("4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1")
        self.assertNotIn("e2d2", moves)
        self.assertIn("e2e8", moves)

    def test_king_cannot_move_into_check(self):
        moves = self.move_strings("4r1k1/8/8/8/8/8/4r3/4K3 w - - 0 1")
        self.assertNotIn("e1e2", moves)

    def test_castling_through_check_is_illegal(self):
        moves = self.move_strings("4kr2/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertNotIn("e1g1", moves)

    def test_en_passant_discovered_check_is_illegal(self):
        moves = self.move_strings("k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        self.assertNotIn("e5d6", moves)

    def test_all_four_promotions_are_generated(self):
        moves = self.move_strings("8/P7/8/8/8/8/8/k6K w - - 0 1")
        self.assertTrue({"a7a8q", "a7a8r", "a7a8b", "a7a8n"}.issubset(moves))

    def test_checker_pin_generator_matches_reference_on_random_games(self):
        rng = random.Random(20260804)
        position = position_from_fen(START_FEN)
        checked = 0
        while checked < 250:
            direct = set(generate_legal_moves(position))
            reference = set(generate_legal_moves_reference(position))
            self.assertEqual(direct, reference)
            checked += 1
            if not direct:
                position = position_from_fen(START_FEN)
                continue
            position.make_move(rng.choice(tuple(direct)))
