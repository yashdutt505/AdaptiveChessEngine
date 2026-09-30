"""Compare two fixed-node label runs over the same decision sample."""

import argparse
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.reference_analysis import load_analyzed_jsonl  # noqa: E402


def _identity(row: dict) -> tuple[str, int]:
    return row["game_id"], row["ply"]


def _correlation(left: list[float], right: list[float]) -> float:
    if len(left) < 2:
        return math.nan
    mean_left, mean_right = statistics.mean(left), statistics.mean(right)
    numerator = sum((x - mean_left) * (y - mean_right) for x, y in zip(left, right))
    denominator = math.sqrt(
        sum((x - mean_left) ** 2 for x in left) * sum((y - mean_right) ** 2 for y in right)
    )
    return numerator / denominator if denominator else math.nan


def compare(left: tuple[dict, ...], right: tuple[dict, ...]) -> dict[str, float | int]:
    if [_identity(row) for row in left] != [_identity(row) for row in right]:
        raise ValueError("reference runs do not contain the same decisions in the same order")
    paired = [(a, b) for a, b in zip(left, right) if a["label_eligible"] and b["label_eligible"]]
    if not paired:
        raise ValueError("reference runs have no jointly eligible labels")
    labels_left = [bool(a["large_error"]) for a, _ in paired]
    labels_right = [bool(b["large_error"]) for _, b in paired]
    agreement = sum(a == b for a, b in zip(labels_left, labels_right)) / len(paired)
    p_left = sum(labels_left) / len(paired)
    p_right = sum(labels_right) / len(paired)
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    kappa = (agreement - expected) / (1 - expected) if expected < 1 else math.nan
    losses_left = [float(a["centipawn_loss"]) for a, _ in paired]
    losses_right = [float(b["centipawn_loss"]) for _, b in paired]
    absolute_differences = [abs(a - b) for a, b in zip(losses_left, losses_right)]
    return {
        "rows": len(left),
        "jointly_eligible": len(paired),
        "excluded_at_either_budget": len(left) - len(paired),
        "binary_agreement": agreement,
        "cohen_kappa": kappa,
        "label_flips": sum(a != b for a, b in zip(labels_left, labels_right)),
        "mean_absolute_cpl_difference": statistics.mean(absolute_differences),
        "median_absolute_cpl_difference": statistics.median(absolute_differences),
        "cpl_pearson_correlation": _correlation(losses_left, losses_right),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    args = parser.parse_args()
    report = compare(load_analyzed_jsonl(args.left), load_analyzed_jsonl(args.right))
    for name, value in report.items():
        rendered = f"{value:.4f}" if isinstance(value, float) else str(value)
        print(f"{name}: {rendered}")


if __name__ == "__main__":
    main()
