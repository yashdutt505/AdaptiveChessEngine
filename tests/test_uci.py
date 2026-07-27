import time
import unittest

from engine.constants import BLACK, START_FEN
from engine.fen import position_to_fen
from engine.uci import UCIEngine


class UCITests(unittest.TestCase):
    def setUp(self):
        self.output = []
        self.engine = UCIEngine(self.output.append)

    def tearDown(self):
        self.engine.stop_search()

    def test_handshake(self):
        self.engine.handle_line("uci")
        self.engine.handle_line("isready")
        self.assertTrue(any(line.startswith("id name ") for line in self.output))
        self.assertIn("uciok", self.output)
        self.assertIn("readyok", self.output)

    def test_position_startpos_with_moves(self):
        self.engine.handle_line("position startpos moves e2e4 e7e5 g1f3")
        self.assertEqual(self.engine.position.side_to_move, BLACK)
        self.assertEqual(len(self.engine.position.history), 3)

    def test_position_fen(self):
        fen = "7k/8/8/8/8/8/8/R5K1 w - - 0 1"
        self.engine.handle_line(f"position fen {fen}")
        self.assertEqual(position_to_fen(self.engine.position), fen)

    def test_go_depth_emits_info_and_bestmove(self):
        self.engine.handle_line("position startpos")
        self.engine.handle_line("go depth 1")
        self.assertTrue(self.engine.wait_for_search(timeout=10))
        self.assertTrue(any(line.startswith("info depth 1 ") for line in self.output))
        self.assertTrue(any(line.startswith("bestmove ") for line in self.output))

    def test_stop_interrupts_infinite_search(self):
        self.engine.handle_line("position startpos")
        self.engine.handle_line("go infinite")
        time.sleep(0.05)
        self.engine.handle_line("stop")
        self.assertTrue(any(line.startswith("bestmove ") for line in self.output))

    def test_new_game_restores_start_position(self):
        self.engine.handle_line("position startpos moves e2e4")
        self.engine.handle_line("ucinewgame")
        self.assertEqual(position_to_fen(self.engine.position), START_FEN)

    def test_quit_requests_exit(self):
        self.assertFalse(self.engine.handle_line("quit"))
