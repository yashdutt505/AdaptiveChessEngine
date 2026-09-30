"""Combine compute-matched adaptive match arms with paired uncertainty."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def paired_bootstrap(left: list[float], right: list[float], seed: int = 20260930) -> dict:
    if len(left) != len(right) or not left:
        raise ValueError("paired arms must contain the same positive game count")
    differences = [a - b for a, b in zip(left, right)]
    rng = random.Random(seed)
    estimates = []
    for _ in range(20_000):
        estimates.append(sum(differences[rng.randrange(len(differences))] for _ in differences) / len(differences))
    estimates.sort()
    return {
        "mean_score_difference": sum(differences) / len(differences),
        "bootstrap_95_interval": [estimates[499], estimates[19_499]],
        "probability_difference_above_zero": sum(value > 0 for value in estimates) / len(estimates),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    for arm in ("neutral", "population", "personal", "random"):
        parser.add_argument(f"--{arm}", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = {arm: getattr(args, arm) for arm in ("neutral", "population", "personal", "random")}
    arms = {arm: json.loads(path.read_text(encoding="utf-8")) for arm, path in paths.items()}
    schedules = [[(record["target_white"], record["game"]) for record in result["records"]] for result in arms.values()]
    if any(schedule != schedules[0] for schedule in schedules[1:]):
        raise ValueError("arms do not share the same game/color schedule")
    neutral = [record["score"] for record in arms["neutral"]["records"]]
    report = {
        "experiment": "learned_adaptive_policy_safety_match_v1",
        "claim_boundary": "engine-opponent safety/behaviour test; not a causal test against Yash",
        "arms": {},
        "paired_vs_neutral": {},
    }
    for arm, result in arms.items():
        records = result["records"]
        report["arms"][arm] = {
            "games": len(records), "score": result["score"], "estimated_elo": result["estimated_elo"],
            "wins": sum(record["score"] == 1 for record in records),
            "draws": sum(record["score"] == .5 for record in records),
            "losses": sum(record["score"] == 0 for record in records),
            "target_options": result["target_options"], "target_nodes": result.get("target_nodes"),
        }
        if arm != "neutral":
            report["paired_vs_neutral"][arm] = paired_bootstrap([record["score"] for record in records], neutral)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
