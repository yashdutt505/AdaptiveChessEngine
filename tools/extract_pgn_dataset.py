"""Extract one player's chronological decision dataset from PGN files."""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pgn_dataset import extract_pgn_file, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True)
    parser.add_argument("--player", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    records = extract_pgn_file(args.pgn, args.player)
    if not records:
        parser.error(f"no decisions found for player {args.player!r}")
    write_jsonl(records, args.output)
    games = {record.game_id for record in records}
    splits = Counter(record.split for record in records)
    print(f"Wrote {len(records)} decisions from {len(games)} games to {Path(args.output).resolve()}")
    print("Splits: " + ", ".join(f"{name}={splits[name]}" for name in ("train", "validation", "test")))


if __name__ == "__main__":
    main()
