"""Post-hoc ablation of temporal/rating proxies in personalization results."""

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, paired_game_bootstrap, probability_metrics,
    train_gradient_boosting,
)


def _without(rows, excluded):
    result = copy.deepcopy(rows)
    for row in result:
        for name in excluded:
            row["features"][name] = 0
    return result


def _split(rows, name):
    return tuple(row for row in rows if row["split"] == name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal", required=True)
    parser.add_argument("--population", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    personal_source = load_model_rows(args.personal)
    population_source = load_model_rows(args.population)
    configurations = {
        "without_rating": ("player_rating", "rating_difference"),
        "without_move_number": ("fullmove_number",),
        "without_rating_or_move_number": ("player_rating", "rating_difference", "fullmove_number"),
    }
    report = {
        "analysis": "post-hoc exploratory ablation; not part of primary model selection",
        "configurations": {},
    }
    for name, excluded in configurations.items():
        personal = _without(personal_source, excluded)
        population = _without(population_source, excluded)
        personal_model, personal_parameters, _ = train_gradient_boosting(
            _split(personal, "train"), _split(personal, "validation"),
        )
        population_model, population_parameters, _ = train_gradient_boosting(
            _split(population, "train"), _split(population, "validation"),
        )
        test_rows = _split(personal, "test")
        test_x, test_y = matrix(test_rows)
        personal_probabilities = personal_model.predict_proba(test_x)[:, 1]
        population_probabilities = population_model.predict_proba(test_x)[:, 1]
        report["configurations"][name] = {
            "excluded_features": list(excluded),
            "personal_parameters": personal_parameters,
            "population_parameters": population_parameters,
            "personal_test": probability_metrics(test_y, personal_probabilities),
            "population_test": probability_metrics(test_y, population_probabilities),
            "personal_vs_population_paired_game_bootstrap": paired_game_bootstrap(
                test_rows, test_y, personal_probabilities, population_probabilities,
            ),
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
