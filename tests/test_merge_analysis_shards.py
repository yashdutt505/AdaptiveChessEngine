import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from engine.pgn_dataset import DecisionRecord
from tools.merge_analysis_shards import merge


def decision(game):
    return DecisionRecord(
        1, game, "2024.01.01", 0, "train", "Alice", "white", "Bob", 0, 1,
        "8/8/8/8/8/8/8/8 w - - 0 1", "", "a1a1", "*", "600", 1000, 1000,
    )


def analyzed(item):
    row = {
        "analysis_version": 1, "reference_nodes": 100000,
        "game_id": item.game_id, "ply": item.ply,
        "fen_before": item.fen_before, "played_uci": item.played_uci,
    }
    return json.dumps(row) + "\n"


class MergeAnalysisShardTests(unittest.TestCase):
    def test_merge_restores_input_order_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = (decision("a"), decision("b"))
            input_path = root / "input.jsonl"
            input_path.write_text(
                "".join(json.dumps(asdict(item)) + "\n" for item in records), encoding="utf-8",
            )
            first, second, output = root / "first.jsonl", root / "second.jsonl", root / "out.jsonl"
            first.write_text(analyzed(records[1]), encoding="utf-8")
            second.write_text(analyzed(records[0]), encoding="utf-8")
            self.assertEqual(merge(str(input_path), [str(first), str(second)], str(output), 100000), 2)
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["game_id"] for row in rows], ["a", "b"])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                merge(str(input_path), [str(first), str(first), str(second)], str(output), 100000)

