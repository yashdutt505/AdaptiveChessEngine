"""Laplace-approximated partially pooled logistic opponent model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from sklearn.preprocessing import StandardScaler

from .opponent_models import matrix


@dataclass(slots=True)
class HierarchicalLogisticModel:
    scaler: StandardScaler
    posterior_mean: np.ndarray
    posterior_covariance: np.ndarray
    personal_scale: float
    global_scale: float

    def _design(self, features: np.ndarray, personal: bool) -> np.ndarray:
        standardized = self.scaler.transform(features)
        base = np.column_stack((np.ones(len(standardized)), standardized))
        return np.hstack((base, base if personal else np.zeros_like(base)))

    def predict_proba(self, features: np.ndarray, personal: bool = True) -> np.ndarray:
        design = self._design(features, personal)
        mean = design @ self.posterior_mean
        variance = np.einsum("ij,jk,ik->i", design, self.posterior_covariance, design)
        # Logistic-normal moment approximation; includes parameter uncertainty.
        return expit(mean / np.sqrt(1.0 + np.pi * np.maximum(variance, 0.0) / 8.0))


def fit_hierarchical_logistic(
    population_rows: tuple[dict, ...], personal_rows: tuple[dict, ...],
    personal_scale: float, global_scale: float = 2.5,
) -> HierarchicalLogisticModel:
    if personal_scale <= 0 or global_scale <= 0:
        raise ValueError("prior scales must be positive")
    population_x, population_y = matrix(population_rows)
    personal_x, personal_y = matrix(personal_rows)
    if not len(population_x) or not len(personal_x):
        raise ValueError("population and personal training rows are both required")
    scaler = StandardScaler().fit(np.vstack((population_x, personal_x)))
    population_base = np.column_stack((np.ones(len(population_x)), scaler.transform(population_x)))
    personal_base = np.column_stack((np.ones(len(personal_x)), scaler.transform(personal_x)))
    design = np.vstack((
        np.hstack((population_base, np.zeros_like(population_base))),
        np.hstack((personal_base, personal_base)),
    ))
    labels = np.concatenate((population_y, personal_y)).astype(float)
    width = population_base.shape[1]
    precision = np.concatenate((
        np.full(width, 1.0 / global_scale ** 2),
        np.full(width, 1.0 / personal_scale ** 2),
    ))

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        logits = design @ parameters
        value = np.logaddexp(0.0, logits).sum() - labels @ logits
        value += 0.5 * np.sum(precision * parameters ** 2)
        gradient = design.T @ (expit(logits) - labels) + precision * parameters
        return float(value), gradient

    result = minimize(
        objective, np.zeros(design.shape[1]), jac=True, method="L-BFGS-B",
        options={"maxiter": 1000, "ftol": 1e-10, "gtol": 1e-6},
    )
    if not result.success:
        raise RuntimeError(f"hierarchical optimization failed: {result.message}")
    probabilities = expit(design @ result.x)
    weights = probabilities * (1.0 - probabilities)
    hessian = design.T @ (design * weights[:, None]) + np.diag(precision)
    covariance = np.linalg.inv(hessian)
    return HierarchicalLogisticModel(
        scaler, result.x, covariance, personal_scale, global_scale,
    )


def select_hierarchical_scale(
    population_train: tuple[dict, ...], personal_train: tuple[dict, ...],
    personal_validation: tuple[dict, ...], scales: tuple[float, ...] = (0.1, 0.25, 0.5, 1.0),
):
    from sklearn.metrics import log_loss

    validation_x, validation_y = matrix(personal_validation)
    candidates = []
    for scale in scales:
        model = fit_hierarchical_logistic(population_train, personal_train, scale)
        probabilities = model.predict_proba(validation_x, personal=True)
        candidates.append((log_loss(validation_y, probabilities, labels=[0, 1]), scale, probabilities))
    return min(candidates, key=lambda item: item[0])
