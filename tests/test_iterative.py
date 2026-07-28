import threading
import unittest

from engine.constants import START_FEN
from engine.fen import position_to_fen
from engine.movegen import generate_legal_moves
from engine.search import iterative_deepening
from engine.search import Searcher
from engine.transposition import TranspositionTable
from tests.helpers import position_from_fen


class IterativeDeepeningTests(unittest.TestCase):
    def test_completed_depths_are_reported_in_order(self):
        position = position_from_fen(START_FEN)
        completed = []
        result = iterative_deepening(
            position,
            max_depth=2,
            info_callback=lambda info: completed.append(info.depth),
        )
        self.assertEqual(completed, [1, 2])
        self.assertEqual(result.depth, 2)
        self.assertIn(result.best_move, generate_legal_moves(position))

    def test_time_limit_returns_move_and_restores_position(self):
        position = position_from_fen(START_FEN)
        original = position_to_fen(position)
        result = iterative_deepening(position, max_depth=64, time_limit_ms=30)
        self.assertIn(result.best_move, generate_legal_moves(position))
        self.assertEqual(position_to_fen(position), original)
        self.assertEqual(len(position.history), 0)

    def test_external_stop_is_honored(self):
        position = position_from_fen(START_FEN)
        stop = threading.Event()
        timer = threading.Timer(0.03, stop.set)
        timer.start()
        try:
            result = iterative_deepening(position, max_depth=64, stop_event=stop)
        finally:
            timer.cancel()
        self.assertIn(result.best_move, generate_legal_moves(position))
        self.assertEqual(position_to_fen(position), START_FEN)

    def test_aspiration_search_matches_full_window_result(self):
        full_position = position_from_fen(START_FEN)
        iterative_position = position_from_fen(START_FEN)
        full = Searcher(
            transposition_table=TranspositionTable(4)
        ).search(full_position, 3)
        iterative = iterative_deepening(
            iterative_position,
            max_depth=3,
            transposition_table=TranspositionTable(4),
        )
        self.assertEqual(iterative.best_move, full.best_move)
        self.assertEqual(iterative.score, full.score)
