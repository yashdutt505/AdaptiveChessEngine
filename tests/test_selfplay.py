import unittest

from engine.selfplay import play_fixed_node_game


class SelfPlayTests(unittest.TestCase):
    def test_fixed_node_selfplay_is_legal_and_deterministic(self):
        first = play_fixed_node_game(nodes_per_move=30, max_plies=8)
        second = play_fixed_node_game(nodes_per_move=30, max_plies=8)
        self.assertEqual(first.moves, second.moves)
        self.assertEqual(first.result, "1/2-1/2")
        self.assertEqual(first.reason, "ply limit")
        self.assertEqual(len(first.moves), 8)
        self.assertGreaterEqual(first.nodes, 8 * 30)
