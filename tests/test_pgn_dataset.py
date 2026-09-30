import tempfile
import unittest
from pathlib import Path

from engine.fen import load_fen
from engine.move import move_to_string
from engine.pgn_dataset import extract_player_decisions, parse_pgn, parse_san, write_jsonl
from engine.position import Position


def game(date, white, black, suffix=""):
    return f'''[Event "Test"]
[Site "Chess.com"]
[Date "{date}"]
[White "{white}"]
[Black "{black}"]
[Result "1/2-1/2"]
[WhiteElo "1500"]
[BlackElo "1600"]
[TimeControl "600"]
[Link "https://www.chess.com/game/live/{date.replace('.', '')}{suffix}"]

1. e4 {{[%clk 0:10:00]}} e5 (1... c5) 2. Nf3 Nc6 $1 3. Bb5 a6 1/2-1/2
'''


class PgnDatasetTests(unittest.TestCase):
    def test_san_parser_handles_disambiguation_castling_and_promotion(self):
        position = Position()
        load_fen(position, "4k3/8/8/8/8/5N2/8/1N2K3 w - - 0 1")
        self.assertEqual(move_to_string(parse_san(position, "Nbd2")), "b1d2")
        load_fen(position, "4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        self.assertEqual(move_to_string(parse_san(position, "a8=Q+")), "a7a8q")
        load_fen(position, "4k3/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertEqual(move_to_string(parse_san(position, "O-O")), "e1g1")

    def test_extraction_is_chronological_and_keeps_games_in_one_split(self):
        text = "\n".join([
            game("2024.01.05", "Alice", "Opponent5", "5"),
            game("2024.01.01", "Alice", "Opponent1", "1"),
            game("2024.01.03", "Opponent3", "Alice", "3"),
            game("2024.01.02", "Alice", "Opponent2", "2"),
            game("2024.01.04", "Opponent4", "Alice", "4"),
        ])
        records = extract_player_decisions(parse_pgn(text), "alice")
        by_game = {}
        for record in records:
            by_game.setdefault(record.game_id, set()).add(record.split)
            self.assertTrue(record.fen_before)
            self.assertEqual(record.dataset_version, 1)
        self.assertEqual(len(by_game), 5)
        self.assertTrue(all(len(splits) == 1 for splits in by_game.values()))
        ordered = []
        for record in records:
            if record.game_date not in ordered:
                ordered.append(record.game_date)
        self.assertEqual(ordered, sorted(ordered))
        split_by_date = {record.game_date: record.split for record in records}
        self.assertEqual([split_by_date[date] for date in ordered], ["train", "train", "train", "validation", "test"])

    def test_jsonl_export_is_deterministic(self):
        records = extract_player_decisions(parse_pgn(game("2024.01.01", "Alice", "Bob")), "Alice")
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.jsonl"
            second = Path(directory) / "second.jsonl"
            write_jsonl(records, first)
            write_jsonl(records, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_invalid_or_ambiguous_san_fails_closed(self):
        position = Position()
        load_fen(position, "4k3/8/8/8/8/5N2/8/1N2K3 w - - 0 1")
        with self.assertRaises(ValueError):
            parse_san(position, "Nd2")


if __name__ == "__main__":
    unittest.main()
