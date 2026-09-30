"""Build the versioned opponent-error feature matrix from analyzed decisions."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_model_features import model_row  # noqa: E402
from engine.reference_analysis import load_analyzed_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    analyzed = load_analyzed_jsonl(args.input)
    rows = [model_row(record) for record in analyzed if record.get("label_eligible")]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8",
    )
    labels = Counter(row["large_error"] for row in rows)
    print(
        f"Wrote {len(rows)} eligible rows: large_errors={labels[True]}, "
        f"other={labels[False]}, excluded={len(analyzed) - len(rows)}"
    )


if __name__ == "__main__":
    main()
