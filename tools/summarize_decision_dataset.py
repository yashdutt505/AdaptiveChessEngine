"""Summarize game-level drift in a chronological decision dataset."""

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.reference_analysis import load_decisions_jsonl  # noqa: E402


def _number_summary(values):
    present = [value for value in values if value is not None]
    return {
        "count": len(present),
        "minimum": min(present) if present else None,
        "median": statistics.median(present) if present else None,
        "mean": statistics.mean(present) if present else None,
        "maximum": max(present) if present else None,
    }


def summarize(records) -> dict:
    games = {}
    decision_counts = Counter()
    for record in records:
        games.setdefault(record.game_id, record)
        decision_counts[record.game_id] += 1
    first = tuple(games.values())
    outcomes = Counter()
    for record in first:
        if record.result == "1/2-1/2":
            outcomes["draw"] += 1
        elif (record.result == "1-0") == (record.player_color == "white"):
            outcomes["win"] += 1
        else:
            outcomes["loss"] += 1
    dates = sorted(record.game_date for record in first)
    return {
        "games": len(first),
        "decisions": len(records),
        "date_start": dates[0] if dates else None,
        "date_end": dates[-1] if dates else None,
        "player_rating": _number_summary(record.player_rating for record in first),
        "opponent_rating": _number_summary(record.opponent_rating for record in first),
        "rating_difference": _number_summary(
            record.player_rating - record.opponent_rating
            if record.player_rating is not None and record.opponent_rating is not None else None
            for record in first
        ),
        "decisions_per_game": _number_summary(decision_counts.values()),
        "colors": dict(sorted(Counter(record.player_color for record in first).items())),
        "outcomes": dict(sorted(outcomes.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    records = load_decisions_jsonl(args.input)
    report = {
        "all": summarize(records),
        "splits": {
            split: summarize(tuple(record for record in records if record.split == split))
            for split in ("train", "validation", "test")
        },
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
