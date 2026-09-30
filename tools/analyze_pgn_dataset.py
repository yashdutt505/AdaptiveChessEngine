"""Label extracted PGN decisions with reproducible fixed-node analysis."""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.reference_analysis import (  # noqa: E402
    FixedNodeReferenceEngine, analyze_decision, load_decisions_jsonl,
    write_analyzed_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--nodes", type=int, default=50_000)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    decisions = load_decisions_jsonl(args.input)
    if args.limit is not None:
        decisions = decisions[:max(0, args.limit)]
    analyzed = []
    with FixedNodeReferenceEngine(args.engine, args.nodes) as engine:
        for index, decision in enumerate(decisions, 1):
            analyzed.append(analyze_decision(decision, engine))
            print(f"analyzed {index}/{len(decisions)}", flush=True)
    write_analyzed_jsonl(analyzed, args.output)
    labels = Counter(record.large_error for record in analyzed if record.label_eligible)
    excluded = sum(not record.label_eligible for record in analyzed)
    print(f"Wrote {len(analyzed)} rows: large_errors={labels[True]}, other={labels[False]}, excluded={excluded}")


if __name__ == "__main__":
    main()
