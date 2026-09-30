"""Fit and evaluate the preregistered partially pooled Bayesian model."""

import argparse
import json
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.hierarchical_opponent_model import (  # noqa: E402
    fit_hierarchical_logistic, select_hierarchical_scale,
)
from engine.opponent_model_features import MODEL_FEATURE_SET_ID  # noqa: E402
from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, paired_game_bootstrap, probability_metrics,
)


def _split(rows: tuple[dict, ...], name: str) -> tuple[dict, ...]:
    return tuple(row for row in rows if row["split"] == name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal", required=True)
    parser.add_argument("--population", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    personal = load_model_rows(args.personal)
    population = load_model_rows(args.population)
    personal_splits = {name: _split(personal, name) for name in ("train", "validation", "test")}
    population_splits = {name: _split(population, name) for name in ("train", "validation")}
    if any(not rows for rows in (*personal_splits.values(), *population_splits.values())):
        parser.error("all required chronological splits must be non-empty")

    validation_loss, scale, validation_probabilities = select_hierarchical_scale(
        population_splits["train"], personal_splits["train"], personal_splits["validation"],
    )
    final_model = fit_hierarchical_logistic(
        population_splits["train"] + population_splits["validation"],
        personal_splits["train"] + personal_splits["validation"], scale,
    )
    _, validation_labels = matrix(personal_splits["validation"])
    test_x, test_labels = matrix(personal_splits["test"])
    personal_probabilities = final_model.predict_proba(test_x, personal=True)
    population_probabilities = final_model.predict_proba(test_x, personal=False)
    report = {
        "model": "laplace_hierarchical_bayesian_logistic",
        "feature_set": MODEL_FEATURE_SET_ID,
        "approximation": "MAP plus inverse-Hessian Gaussian posterior",
        "population_rows": len(population),
        "personal_rows": len(personal),
        "parameters": {"personal_prior_scale": scale, "global_prior_scale": 2.5},
        "selection_validation_log_loss": validation_loss,
        "validation": probability_metrics(validation_labels, validation_probabilities),
        "test": probability_metrics(test_labels, personal_probabilities),
        "population_fallback_test": probability_metrics(test_labels, population_probabilities),
        "personal_vs_population_paired_game_bootstrap": paired_game_bootstrap(
            personal_splits["test"], test_labels, personal_probabilities, population_probabilities,
        ),
    }
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, output / "hierarchical_bayesian_logistic.joblib")
    (output / "hierarchical_model_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
