"""Label extracted PGN decisions with reproducible fixed-node analysis."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.reference_analysis import (  # noqa: E402
    FixedNodeReferenceEngine, analyze_decision, deterministic_decision_sample,
    deterministic_game_sample, load_analyzed_jsonl, load_decisions_jsonl,
    validate_resume_prefix,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--nodes", type=int, default=50_000)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sample-size", type=int)
    parser.add_argument("--sample-games", type=int)
    parser.add_argument("--include-split", action="append", choices=("train", "validation", "test"))
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    decisions = load_decisions_jsonl(args.input)
    if args.include_split:
        included = set(args.include_split)
        decisions = tuple(decision for decision in decisions if decision.split in included)
    if args.sample_games is not None:
        decisions = deterministic_game_sample(decisions, args.sample_games)
    if args.sample_size is not None:
        decisions = deterministic_decision_sample(decisions, args.sample_size)
    if args.limit is not None:
        decisions = decisions[:max(0, args.limit)]
    if args.start_index < 0 or (args.end_index is not None and args.end_index < args.start_index):
        parser.error("analysis index range is invalid")
    decisions = decisions[args.start_index:args.end_index]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    existing = load_analyzed_jsonl(output) if args.resume and output.exists() else ()
    validate_resume_prefix(decisions, existing, args.nodes)
    if not args.resume:
        output.write_text("", encoding="utf-8")
    start = len(existing)
    if start:
        print(f"resuming after {start}/{len(decisions)} completed rows", flush=True)
    counts = Counter(row.get("large_error") for row in existing if row.get("label_eligible"))
    excluded = sum(not row.get("label_eligible") for row in existing)
    with FixedNodeReferenceEngine(args.engine, args.nodes) as engine:
        with output.open("a", encoding="utf-8") as stream:
            for index, decision in enumerate(decisions[start:], start + 1):
                analyzed = analyze_decision(decision, engine)
                stream.write(json.dumps(analyzed.to_dict(), sort_keys=True) + "\n")
                stream.flush()
                if analyzed.label_eligible:
                    counts[analyzed.large_error] += 1
                else:
                    excluded += 1
                if index % 100 == 0 or index == len(decisions):
                    print(f"analyzed {index}/{len(decisions)}", flush=True)
    print(f"Wrote {len(decisions)} rows: large_errors={counts[True]}, other={counts[False]}, excluded={excluded}")


if __name__ == "__main__":
    main()
