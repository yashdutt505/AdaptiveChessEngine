"""Validate and merge fixed-node analysis shards into original input order."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.reference_analysis import (  # noqa: E402
    ANALYSIS_VERSION, load_analyzed_jsonl, load_decisions_jsonl,
)


def identity(row) -> tuple[str, int, str, str]:
    return row.game_id, row.ply, row.fen_before, row.played_uci


def merge(input_path: str, shard_paths: list[str], output_path: str, nodes: int) -> int:
    decisions = load_decisions_jsonl(input_path)
    indexed = {}
    for path in shard_paths:
        for row in load_analyzed_jsonl(path):
            key = (row.get("game_id"), row.get("ply"), row.get("fen_before"), row.get("played_uci"))
            if key in indexed:
                raise ValueError(f"duplicate analyzed decision in shards: {key[:2]}")
            if row.get("analysis_version") != ANALYSIS_VERSION or row.get("reference_nodes") != nodes:
                raise ValueError(f"incompatible analysis configuration in {path}")
            indexed[key] = row
    expected = [identity(decision) for decision in decisions]
    expected_set = set(expected)
    missing = [key for key in expected if key not in indexed]
    extras = [key for key in indexed if key not in expected_set]
    if missing or extras:
        raise ValueError(f"shards do not exactly cover input: missing={len(missing)}, extras={len(extras)}")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(indexed[key], sort_keys=True) + "\n" for key in expected), encoding="utf-8",
    )
    return len(expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--shard", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--nodes", type=int, required=True)
    args = parser.parse_args()
    rows = merge(args.input, args.shard, args.output, args.nodes)
    print(f"Merged {rows} validated rows into {Path(args.output).resolve()}")


if __name__ == "__main__":
    main()
