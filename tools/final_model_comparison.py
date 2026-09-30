"""Produce final paired model comparisons and post-hoc feature evidence."""

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_model_features import MODEL_FEATURE_NAMES  # noqa: E402
from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, paired_game_bootstrap, probability_metrics,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = load_model_rows(args.personal)
    test_rows = tuple(row for row in rows if row["split"] == "test")
    test_x, test_y = matrix(test_rows)
    model_dir = Path(args.model_dir)
    logistic = joblib.load(model_dir / "regularized_logistic.joblib")
    boosting = joblib.load(model_dir / "hist_gradient_boosting.joblib")
    hierarchical = joblib.load(model_dir / "hierarchical_bayesian_logistic.joblib")
    probabilities = {
        "regularized_logistic": logistic.predict_proba(test_x)[:, 1],
        "hist_gradient_boosting": boosting.predict_proba(test_x)[:, 1],
        "hierarchical_bayesian_logistic": hierarchical.predict_proba(test_x, personal=True),
    }
    report = {
        "test_rows": len(test_rows),
        "models": {name: probability_metrics(test_y, values) for name, values in probabilities.items()},
        "paired_comparisons": {},
    }
    for control in ("regularized_logistic", "hierarchical_bayesian_logistic"):
        report["paired_comparisons"][f"hist_gradient_boosting_vs_{control}"] = paired_game_bootstrap(
            test_rows, test_y, probabilities["hist_gradient_boosting"], probabilities[control],
        )

    classifier = logistic.named_steps["logisticregression"]
    report["standardized_logistic_coefficients"] = dict(sorted(
        zip(MODEL_FEATURE_NAMES, classifier.coef_[0]), key=lambda item: abs(item[1]), reverse=True,
    ))
    # Exploratory post-hoc importance on the held-out set; not used for selection.
    importance = permutation_importance(
        boosting, test_x, test_y, scoring="neg_log_loss", n_repeats=10,
        random_state=20260930, n_jobs=1,
    )
    report["posthoc_test_permutation_importance_log_loss"] = dict(sorted(
        zip(MODEL_FEATURE_NAMES, importance.importances_mean),
        key=lambda item: item[1], reverse=True,
    ))
    report["interpretation_warning"] = (
        "Permutation importance is post-hoc, feature-correlated, and descriptive; "
        "it was not used for model selection or causal claims."
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
