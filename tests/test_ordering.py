import unittest

from engine.constants import START_FEN, WHITE
from engine.move import move_to_string
from engine.ordering import SearchHeuristics
from engine.search import Searcher
from tests.helpers import legal_move, position_from_fen


class MoveOrderingTests(unittest.TestCase):
    def test_quiet_cutoff_records_killer_and_history(self):
        position = position_from_fen(START_FEN)
        move = legal_move(position, "e2e4")
        heuristics = SearchHeuristics()
        heuristics.record_cutoff(move, depth=4, ply=2, color=WHITE, move_index=0)
        self.assertEqual(heuristics.killer_rank(move, 2), 2)
        self.assertEqual(heuristics.history_score(move, WHITE), 16)
        self.assertEqual(heuristics.beta_cutoffs, 1)
        self.assertEqual(heuristics.first_move_cutoffs, 1)

    def test_two_killer_slots_keep_most_recent_moves(self):
        position = position_from_fen(START_FEN)
        first = legal_move(position, "e2e4")
        second = legal_move(position, "d2d4")
        heuristics = SearchHeuristics()
        heuristics.record_cutoff(first, 2, 3, WHITE, 1)
        heuristics.record_cutoff(second, 2, 3, WHITE, 1)
        self.assertEqual(heuristics.killer_rank(second, 3), 2)
        self.assertEqual(heuristics.killer_rank(first, 3), 1)

    def test_remembered_quiet_move_is_ordered_first(self):
        position = position_from_fen(START_FEN)
        moves = [
            legal_move(position, "a2a3"),
            legal_move(position, "e2e4"),
            legal_move(position, "d2d4"),
        ]
        heuristics = SearchHeuristics()
        heuristics.record_cutoff(moves[1], 4, 2, WHITE, 1)
        searcher = Searcher(heuristics=heuristics)
        ordered = searcher._ordered_moves(position, moves, ply=2, color=WHITE)
        self.assertEqual(move_to_string(ordered[0]), "e2e4")
