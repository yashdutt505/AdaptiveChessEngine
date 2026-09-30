"""Compare target-trained models with same-class population fallbacks."""

import argparse
import json
import sys
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, paired_game_bootstrap, probability_metrics,
    train_gradient_boosting, train_logistic,
)


def _split(rows, name):
    return tuple(row for row in rows if row["split"] == name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal", required=True)
    parser.add_argument("--population", required=True)
    parser.add_argument("--personal-model-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    personal = load_model_rows(args.personal)
    population = load_model_rows(args.population)
    personal_test = _split(personal, "test")
    test_x, test_y = matrix(personal_test)
    population_train = _split(population, "train")
    population_validation = _split(population, "validation")
    if not personal_test or not population_train or not population_validation:
        parser.error("personal test and population train/validation splits are required")

    model_dir = Path(args.personal_model_dir)
    definitions = {
        "regularized_logistic": train_logistic,
        "hist_gradient_boosting": train_gradient_boosting,
    }
    report = {
        "comparison": "personal_training_vs_population_training_on_identical_personal_test_rows",
        "personal_test_rows": len(personal_test),
        "population_train_rows": len(population_train),
        "population_validation_rows": len(population_validation),
        "models": {},
    }
    for name, trainer in definitions.items():
        personal_model = joblib.load(model_dir / f"{name}.joblib")
        population_model, parameters, _ = trainer(population_train, population_validation)
        personal_probabilities = personal_model.predict_proba(test_x)[:, 1]
        population_probabilities = population_model.predict_proba(test_x)[:, 1]
        report["models"][name] = {
            "population_parameters": parameters,
            "personal_test": probability_metrics(test_y, personal_probabilities),
            "population_fallback_test": probability_metrics(test_y, population_probabilities),
            "personal_vs_population_paired_game_bootstrap": paired_game_bootstrap(
                personal_test, test_y, personal_probabilities, population_probabilities,
            ),
        }
        joblib.dump(population_model, model_dir / f"population_{name}.joblib")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
