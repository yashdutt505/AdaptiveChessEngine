"""Extract one player's chronological decision dataset from PGN files."""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.pgn_dataset import (  # noqa: E402
    extract_all_decisions, extract_pgn_file, parse_pgn, write_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pgn", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--player")
    group.add_argument("--all-players", action="store_true")
    parser.add_argument("--exclude-player")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.player:
        if args.exclude_player:
            parser.error("--exclude-player requires --all-players")
        records = extract_pgn_file(args.pgn, args.player)
    else:
        games_in_file = parse_pgn(Path(args.pgn).read_text(encoding="utf-8-sig"))
        records = extract_all_decisions(games_in_file, args.exclude_player)
    if not records:
        parser.error("no decisions found")
    write_jsonl(records, args.output)
    games = {record.game_id for record in records}
    splits = Counter(record.split for record in records)
    print(f"Wrote {len(records)} decisions from {len(games)} games to {Path(args.output).resolve()}")
    print("Splits: " + ", ".join(f"{name}={splits[name]}" for name in ("train", "validation", "test")))


if __name__ == "__main__":
    main()
