"""Fit the preregistered personal logistic and gradient-boosted models once."""

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_model_features import MODEL_FEATURE_NAMES, MODEL_FEATURE_SET_ID  # noqa: E402
from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, probability_metrics, train_gradient_boosting, train_logistic,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    rows = load_model_rows(args.input)
    splits = {name: tuple(row for row in rows if row["split"] == name) for name in ("train", "validation", "test")}
    if any(not values for values in splits.values()):
        parser.error("train, validation, and test splits must all be non-empty")

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    _, train_labels = matrix(splits["train"])
    test_x, test_labels = matrix(splits["test"])
    prevalence = float(train_labels.mean())
    report = {
        "feature_set": MODEL_FEATURE_SET_ID,
        "features": list(MODEL_FEATURE_NAMES),
        "selection_metric": "validation_log_loss",
        "test_policy": "evaluated once after validation selection",
        "splits": {
            name: {"rows": len(values), "games": len({row["game_id"] for row in values})}
            for name, values in splits.items()
        },
        "models": {
            "constant_train_prevalence": {
                "parameters": {"probability": prevalence},
                "test": probability_metrics(test_labels, np.full(len(test_labels), prevalence)),
            },
        },
    }
    trainers = {
        "regularized_logistic": train_logistic,
        "hist_gradient_boosting": train_gradient_boosting,
    }
    for name, trainer in trainers.items():
        model, parameters, validation_probabilities = trainer(splits["train"], splits["validation"])
        _, validation_labels = matrix(splits["validation"])
        report["models"][name] = {
            "parameters": parameters,
            "validation": probability_metrics(validation_labels, validation_probabilities),
            "test": probability_metrics(test_labels, model.predict_proba(test_x)[:, 1]),
        }
        joblib.dump(model, output / f"{name}.joblib")

    (output / "personal_model_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
