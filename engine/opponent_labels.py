"""Versioned supervised targets for opponent-error modelling."""

from __future__ import annotations

from dataclasses import dataclass


LABEL_VERSION = 1
DEFAULT_LARGE_ERROR_THRESHOLD_CP = 100


@dataclass(frozen=True, slots=True)
class DecisionLabel:
    """Label for one opponent decision, with both scores in pre-move POV."""

    version: int
    threshold_cp: int
    eligible: bool
    centipawn_loss: int | None
    large_error: bool | None
    exclusion_reason: str | None


def label_decision(
    best_score_cp: int,
    played_score_cp: int,
    *,
    threshold_cp: int = DEFAULT_LARGE_ERROR_THRESHOLD_CP,
    best_is_mate: bool = False,
    played_is_mate: bool = False,
) -> DecisionLabel:
    """Return whether the played move lost at least ``threshold_cp``.

    Both evaluations must use the opponent's perspective immediately before
    their move. Mate-score decisions are excluded from v1 because mate distance
    is not a stable centipawn quantity; they will receive a separate target.
    """
    for value, name in ((best_score_cp, "best_score_cp"), (played_score_cp, "played_score_cp")):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer")
    if isinstance(threshold_cp, bool) or not isinstance(threshold_cp, int) or threshold_cp <= 0:
        raise ValueError("threshold_cp must be a positive integer")
    if best_is_mate or played_is_mate:
        return DecisionLabel(LABEL_VERSION, threshold_cp, False, None, None, "mate-score")
    centipawn_loss = max(0, best_score_cp - played_score_cp)
    return DecisionLabel(
        LABEL_VERSION,
        threshold_cp,
        True,
        centipawn_loss,
        centipawn_loss >= threshold_cp,
        None,
    )
