import unittest

from engine.epd import parse_epd_line, run_epd_cases


class EPDTests(unittest.TestCase):
    def test_parse_and_solve_best_move_case(self):
        case = parse_epd_line(
            '7k/6pp/8/8/8/8/5PPP/3Q2K1 w - - bm d1d8; id "mate one";'
        )
        self.assertEqual(case.name, "mate one")
        self.assertEqual(case.best_moves, frozenset({"d1d8"}))
        result = run_epd_cases([case], nodes_per_case=500)[0]
        self.assertTrue(result["passed"])

    def test_comments_and_invalid_lines(self):
        self.assertIsNone(parse_epd_line("# comment"))
        with self.assertRaises(ValueError):
            parse_epd_line("8/8/8/8/8/8/8/8 w - -")
