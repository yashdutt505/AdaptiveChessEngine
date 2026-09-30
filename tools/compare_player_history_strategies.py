"""Compare population, lifetime, recent, decayed, and online opponent models."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import log_loss
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.opponent_models import (  # noqa: E402
    load_model_rows, matrix, paired_game_bootstrap, probability_metrics,
)


DEFAULT_PARAMETERS = {
    "learning_rate": 0.03,
    "max_leaf_nodes": 7,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "max_iter": 300,
}


def games_in_order(rows: tuple[dict, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(row["game_id"] for row in rows))


def latest_games(rows: tuple[dict, ...], count: int) -> tuple[dict, ...]:
    games = games_in_order(rows)
    selected = set(games[-count:])
    return tuple(row for row in rows if row["game_id"] in selected)


def recency_weights(rows: tuple[dict, ...], half_life_games: float) -> np.ndarray:
    if half_life_games <= 0:
        raise ValueError("half life must be positive")
    games = games_in_order(rows)
    order = {game: index for index, game in enumerate(games)}
    latest = len(games) - 1
    return np.asarray([
        math.exp(-math.log(2.0) * (latest - order[row["game_id"]]) / half_life_games)
        for row in rows
    ])


def fit_boosting(rows: tuple[dict, ...], sample_weight: np.ndarray | None = None):
    features, labels = matrix(rows)
    model = HistGradientBoostingClassifier(random_state=20260930, early_stopping=False, **DEFAULT_PARAMETERS)
    with threadpool_limits(limits=1):
        model.fit(features, labels, sample_weight=sample_weight)
    return model


def predict(model, rows: tuple[dict, ...]) -> np.ndarray:
    features, _ = matrix(rows)
    return model.predict_proba(features)[:, 1]


def validation_choice(train: tuple[dict, ...], validation: tuple[dict, ...]):
    _, labels = matrix(validation)
    lifetime = float(log_loss(labels, predict(fit_boosting(train), validation), labels=[0, 1]))
    windows = {}
    for count in (100, 200, 300):
        selected = latest_games(train, count)
        probabilities = predict(fit_boosting(selected), validation)
        windows[count] = float(log_loss(labels, probabilities, labels=[0, 1]))
    decays = {}
    for half_life in (50, 100, 200, 400):
        probabilities = predict(fit_boosting(train, recency_weights(train, half_life)), validation)
        decays[half_life] = float(log_loss(labels, probabilities, labels=[0, 1]))
    best_window = min(windows, key=windows.get)
    best_decay = min(decays, key=decays.get)
    strategies = {
        "lifetime_personal": lifetime,
        "recent_window_personal": windows[best_window],
        "time_decayed_personal": decays[best_decay],
    }
    return best_window, best_decay, min(strategies, key=strategies.get), lifetime, windows, decays


def online_predictions(
    history: tuple[dict, ...], test: tuple[dict, ...], batch_games: int,
    strategy: str, window_games: int, half_life_games: int,
) -> tuple[np.ndarray, list[dict]]:
    if batch_games < 1:
        raise ValueError("batch_games must be positive")
    test_games = games_in_order(test)
    predictions = np.empty(len(test), dtype=float)
    batches = []
    test_indices = {game: np.asarray([i for i, row in enumerate(test) if row["game_id"] == game]) for game in test_games}
    available = list(history)
    for start in range(0, len(test_games), batch_games):
        batch = test_games[start:start + batch_games]
        training = tuple(available)
        if strategy == "recent_window":
            training = latest_games(training, window_games)
            weights = None
        elif strategy == "time_decayed":
            weights = recency_weights(training, half_life_games)
        else:
            weights = None
        model = fit_boosting(training, weights)
        selected_indices = np.concatenate([test_indices[game] for game in batch])
        batch_rows = tuple(test[index] for index in selected_indices)
        predictions[selected_indices] = predict(model, batch_rows)
        batches.append({
            "first_game_index": start,
            "games": len(batch),
            "training_games": len(games_in_order(training)),
            "prediction_rows": len(batch_rows),
        })
        available.extend(batch_rows)
    return predictions, batches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--personal-rows", required=True)
    parser.add_argument("--population-model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-output-dir", required=True)
    parser.add_argument("--online-batch-games", type=int, default=20)
    args = parser.parse_args()

    rows = load_model_rows(args.personal_rows)
    train = tuple(row for row in rows if row["split"] == "train")
    validation = tuple(row for row in rows if row["split"] == "validation")
    test = tuple(row for row in rows if row["split"] == "test")
    if not train or not validation or not test:
        parser.error("all chronological splits are required")

    window, half_life, selected_strategy, lifetime_score, window_scores, decay_scores = validation_choice(train, validation)
    history = train + validation
    _, labels = matrix(test)
    models = {}
    probabilities = {}

    models["population"] = joblib.load(args.population_model)
    probabilities["population"] = predict(models["population"], test)
    models["lifetime_personal"] = fit_boosting(history)
    probabilities["lifetime_personal"] = predict(models["lifetime_personal"], test)
    recent_rows = latest_games(history, window)
    models["recent_window_personal"] = fit_boosting(recent_rows)
    probabilities["recent_window_personal"] = predict(models["recent_window_personal"], test)
    models["time_decayed_personal"] = fit_boosting(history, recency_weights(history, half_life))
    probabilities["time_decayed_personal"] = predict(models["time_decayed_personal"], test)

    online, batches = online_predictions(
        history, test, args.online_batch_games,
        "recent_window" if selected_strategy == "recent_window_personal" else
        "time_decayed" if selected_strategy == "time_decayed_personal" else "lifetime",
        window, half_life,
    )
    probabilities["online_personal"] = online

    output_dir = Path(args.model_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        joblib.dump(model, output_dir / f"{name}.joblib")

    report = {
        "experiment": "chronological_player_history_strategy_comparison_v1",
        "selection_boundary": "window and decay selected on validation only",
        "fixed_boosting_parameters": DEFAULT_PARAMETERS,
        "selected_recent_window_games": window,
        "selected_decay_half_life_games": half_life,
        "validation_log_loss": {
            "lifetime": lifetime_score,
            "recent_windows": {str(k): v for k, v in window_scores.items()},
            "decay_half_lives": {str(k): v for k, v in decay_scores.items()},
        },
        "test_games": len(games_in_order(test)),
        "test_rows": len(test),
        "selected_frozen_strategy": selected_strategy,
        "online_update_policy": {
            "base_strategy": selected_strategy,
            "batch_games": args.online_batch_games,
            "batches": batches,
        },
        "models": {},
    }
    for name, values in probabilities.items():
        entry = {"test": probability_metrics(labels, values)}
        if name != "population":
            entry["vs_population_paired_game_bootstrap"] = paired_game_bootstrap(
                test, labels, values, probabilities["population"]
            )
        if name != selected_strategy and name not in ("population", "online_personal"):
            entry["vs_selected_frozen_strategy_paired_game_bootstrap"] = paired_game_bootstrap(
                test, labels, values, probabilities[selected_strategy]
            )
        report["models"][name] = entry

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
