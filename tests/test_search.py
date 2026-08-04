import unittest

from engine.attacks import is_in_check
from engine.fen import position_to_fen
from engine.move import move_to_string
from engine.movegen import generate_legal_moves
from engine.search import MATE_SCORE, Searcher
from tests.helpers import position_from_fen


class SearchTests(unittest.TestCase):
    def test_invalid_search_window_is_rejected(self):
        position = position_from_fen("7k/8/8/8/8/8/8/R5K1 w - - 0 1")
        with self.assertRaises(ValueError):
            Searcher().search(position, 2, alpha=10, beta=10)

    def test_search_finds_mate_in_one(self):
        position = position_from_fen("7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - 0 1")
        result = Searcher().search(position, 2)
        self.assertIsNotNone(result.best_move)
        position.make_move(result.best_move)
        self.assertEqual(generate_legal_moves(position), [])
        self.assertTrue(is_in_check(position))
        position.unmake_move()
        self.assertGreaterEqual(result.score, MATE_SCORE - 2)

    def test_search_takes_hanging_queen(self):
        position = position_from_fen("q6k/8/8/8/8/8/8/R5K1 w - - 0 1")
        result = Searcher().search(position, 1)
        self.assertEqual(move_to_string(result.best_move), "a1a8")

    def test_checkmate_and_stalemate_scores(self):
        checkmate = position_from_fen("7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        stalemate = position_from_fen("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        self.assertLessEqual(Searcher().search(checkmate, 1).score, -MATE_SCORE)
        self.assertEqual(Searcher().search(stalemate, 1).score, 0)

    def test_search_restores_position(self):
        position = position_from_fen(
            "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        )
        fen = position_to_fen(position)
        hash_key = position.hash_key
        history_size = len(position.history)
        result = Searcher().search(position, 2)
        self.assertIn(result.best_move, generate_legal_moves(position))
        self.assertEqual(position_to_fen(position), fen)
        self.assertEqual(position.hash_key, hash_key)
        self.assertEqual(len(position.history), history_size)
        self.assertTrue(result.pv)

    def test_claimable_draw_still_returns_a_legal_move(self):
        position = position_from_fen("7k/8/8/8/8/8/8/R5K1 w - - 100 51")
        legal = generate_legal_moves(position)
        result = Searcher().search(position, 2)
        self.assertIn(result.best_move, legal)
        self.assertEqual(result.score, 0)

    def test_pvs_preserves_full_width_result(self):
        position = position_from_fen(
            "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 3"
        )
        baseline = Searcher(enable_pvs=False).search(position, 3)
        optimized = Searcher(enable_pvs=True).search(position, 3)
        self.assertEqual(optimized.score, baseline.score)
        self.assertEqual(optimized.best_move, baseline.best_move)

    def test_safe_quiescence_pruning_preserves_tactical_result(self):
        position = position_from_fen(
            "3r2k1/3q1ppp/8/3p4/3Q4/8/5PPP/3R2K1 w - - 0 1"
        )
        baseline = Searcher(enable_q_pruning=False).search(position, 2)
        optimized = Searcher(enable_q_pruning=True).search(position, 2)
        self.assertEqual(optimized.score, baseline.score)
        self.assertEqual(optimized.best_move, baseline.best_move)
