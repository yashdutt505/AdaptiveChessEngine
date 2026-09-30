"""Training and evaluation utilities for opponent-error probability models."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, brier_score_loss, log_loss, roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .opponent_model_features import MODEL_FEATURE_NAMES, MODEL_FEATURE_SET_ID


def load_model_rows(path: str | Path) -> tuple[dict, ...]:
    rows = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("feature_set") != MODEL_FEATURE_SET_ID:
            raise ValueError(f"unsupported feature set at line {line_number}")
        if set(row["features"]) != set(MODEL_FEATURE_NAMES):
            raise ValueError(f"feature fields mismatch at line {line_number}")
        rows.append(row)
    return tuple(rows)


def matrix(rows: tuple[dict, ...]) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray([[row["features"][name] for name in MODEL_FEATURE_NAMES] for row in rows], dtype=float),
        np.asarray([row["large_error"] for row in rows], dtype=int),
    )


def expected_calibration_error(labels: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    boundaries = np.linspace(0.0, 1.0, bins + 1)
    total = len(labels)
    error = 0.0
    for index in range(bins):
        lower, upper = boundaries[index], boundaries[index + 1]
        selected = (probabilities >= lower) & (
            probabilities <= upper if index == bins - 1 else probabilities < upper
        )
        if selected.any():
            error += selected.mean() * abs(labels[selected].mean() - probabilities[selected].mean())
    return float(error) if total else math.nan


def probability_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float | int]:
    if len(labels) == 0:
        raise ValueError("cannot evaluate an empty split")
    return {
        "rows": len(labels),
        "prevalence": float(labels.mean()),
        "log_loss": float(log_loss(labels, probabilities, labels=[0, 1])),
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "roc_auc": float(roc_auc_score(labels, probabilities)) if len(np.unique(labels)) == 2 else math.nan,
        "average_precision": float(average_precision_score(labels, probabilities)),
        "ece_10": expected_calibration_error(labels, probabilities),
    }


def paired_game_bootstrap(
    rows: tuple[dict, ...], labels: np.ndarray, treatment: np.ndarray, control: np.ndarray,
    repetitions: int = 2000, seed: int = 20260930,
) -> dict[str, dict[str, float]]:
    """Paired cluster bootstrap; negative loss differences favor treatment."""
    if not (len(rows) == len(labels) == len(treatment) == len(control)):
        raise ValueError("bootstrap inputs must have equal length")
    if repetitions < 1:
        raise ValueError("bootstrap repetitions must be positive")
    game_ids = np.asarray([row["game_id"] for row in rows])
    games = np.unique(game_ids)
    if not len(games):
        raise ValueError("bootstrap requires at least one game")
    indices = {game: np.flatnonzero(game_ids == game) for game in games}
    rng = np.random.default_rng(seed)

    def differences(selected: np.ndarray) -> tuple[float, float]:
        y = labels[selected]
        p_treatment = np.clip(treatment[selected], 1e-12, 1 - 1e-12)
        p_control = np.clip(control[selected], 1e-12, 1 - 1e-12)
        treatment_log = -np.mean(y * np.log(p_treatment) + (1 - y) * np.log(1 - p_treatment))
        control_log = -np.mean(y * np.log(p_control) + (1 - y) * np.log(1 - p_control))
        treatment_brier = np.mean((y - p_treatment) ** 2)
        control_brier = np.mean((y - p_control) ** 2)
        return float(treatment_log - control_log), float(treatment_brier - control_brier)

    point = differences(np.arange(len(rows)))
    samples = np.empty((repetitions, 2))
    for repetition in range(repetitions):
        sampled_games = rng.choice(games, size=len(games), replace=True)
        selected = np.concatenate([indices[game] for game in sampled_games])
        samples[repetition] = differences(selected)
    result = {}
    for column, name in enumerate(("log_loss_difference", "brier_score_difference")):
        result[name] = {
            "point": point[column],
            "ci95_low": float(np.quantile(samples[:, column], 0.025)),
            "ci95_high": float(np.quantile(samples[:, column], 0.975)),
            "probability_treatment_better": float(np.mean(samples[:, column] < 0)),
        }
    return result


def train_logistic(train_rows: tuple[dict, ...], validation_rows: tuple[dict, ...]):
    x_train, y_train = matrix(train_rows)
    x_validation, y_validation = matrix(validation_rows)
    candidates = []
    for regularization in (0.01, 0.1, 1.0, 10.0):
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(C=regularization, max_iter=2000, random_state=20260930),
        )
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_validation)[:, 1]
        candidates.append((log_loss(y_validation, probabilities, labels=[0, 1]), regularization, model))
    _, regularization, selection_model = min(candidates, key=lambda item: item[0])
    validation_probabilities = selection_model.predict_proba(x_validation)[:, 1]
    final_model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=regularization, max_iter=2000, random_state=20260930),
    )
    final_model.fit(np.vstack((x_train, x_validation)), np.concatenate((y_train, y_validation)))
    return final_model, {"C": regularization}, validation_probabilities


def train_gradient_boosting(train_rows: tuple[dict, ...], validation_rows: tuple[dict, ...]):
    x_train, y_train = matrix(train_rows)
    x_validation, y_validation = matrix(validation_rows)
    candidates = []
    for learning_rate in (0.03, 0.1):
        for leaf_nodes in (7, 15, 31):
            for minimum_leaf in (20, 50):
                model = HistGradientBoostingClassifier(
                    learning_rate=learning_rate,
                    max_leaf_nodes=leaf_nodes,
                    min_samples_leaf=minimum_leaf,
                    l2_regularization=1.0,
                    max_iter=300,
                    early_stopping=False,
                    random_state=20260930,
                )
                model.fit(x_train, y_train)
                probabilities = model.predict_proba(x_validation)[:, 1]
                candidates.append((
                    log_loss(y_validation, probabilities, labels=[0, 1]),
                    learning_rate, leaf_nodes, minimum_leaf, model,
                ))
    _, learning_rate, leaf_nodes, minimum_leaf, selection_model = min(candidates, key=lambda item: item[0])
    validation_probabilities = selection_model.predict_proba(x_validation)[:, 1]
    final_model = HistGradientBoostingClassifier(
        learning_rate=learning_rate,
        max_leaf_nodes=leaf_nodes,
        min_samples_leaf=minimum_leaf,
        l2_regularization=1.0,
        max_iter=300,
        early_stopping=False,
        random_state=20260930,
    )
    final_model.fit(np.vstack((x_train, x_validation)), np.concatenate((y_train, y_validation)))
    return final_model, {
        "learning_rate": learning_rate,
        "max_leaf_nodes": leaf_nodes,
        "min_samples_leaf": minimum_leaf,
        "l2_regularization": 1.0,
    }, validation_probabilities
