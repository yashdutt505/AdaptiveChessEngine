"""Strict, versioned opponent-profile contract for the adaptive layer."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_ID = "ace.opponent-profile"
SCHEMA_VERSION = 1
FEATURE_SET_VERSION = 1
FEATURE_NAMES = (
    "capture_value_cp",
    "promotion_gain_cp",
    "gives_check",
    "legal_reply_count",
    "material_balance_cp",
    "material_imbalance_cp",
    "remaining_non_pawn_material_cp",
    "remaining_pawn_count",
    "open_file_count",
    "mobility_balance",
    "king_safety_balance",
    "pawn_structure_balance",
    "center_control_balance",
    "pawn_tension_count",
    "irreversible",
    "castles",
)
PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SOURCES = frozenset({"neutral", "synthetic", "pgn"})


@dataclass(frozen=True, slots=True)
class ProfileProvenance:
    source: str
    games: int
    positions: int
    notes: str = ""


@dataclass(frozen=True, slots=True)
class OpponentProfile:
    profile_id: str
    display_name: str
    created_at: str
    provenance: ProfileProvenance
    feature_weights: tuple[tuple[str, int], ...]
    feature_confidence: tuple[tuple[str, int], ...]
    schema: str = SCHEMA_ID
    schema_version: int = SCHEMA_VERSION
    feature_set_version: int = FEATURE_SET_VERSION

    def weight(self, feature: str) -> int:
        return dict(self.feature_weights)[feature]

    def confidence(self, feature: str) -> int:
        return dict(self.feature_confidence)[feature]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "feature_set_version": self.feature_set_version,
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "provenance": {
                "source": self.provenance.source,
                "games": self.provenance.games,
                "positions": self.provenance.positions,
                "notes": self.provenance.notes,
            },
            "feature_weights": dict(self.feature_weights),
            "feature_confidence": dict(self.feature_confidence),
        }


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate profile field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite profile number: {value}")


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def _exact_keys(value: Any, expected: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ValueError(f"{name} fields mismatch; missing={missing}, unknown={unknown}")
    return value


def profile_from_dict(value: Any) -> OpponentProfile:
    fields = {
        "schema", "schema_version", "feature_set_version", "profile_id",
        "display_name", "created_at", "provenance", "feature_weights",
        "feature_confidence",
    }
    data = _exact_keys(value, fields, "profile")
    if data["schema"] != SCHEMA_ID:
        raise ValueError(f"unsupported profile schema: {data['schema']!r}")
    _integer(data["schema_version"], "schema_version", SCHEMA_VERSION, SCHEMA_VERSION)
    _integer(data["feature_set_version"], "feature_set_version", FEATURE_SET_VERSION, FEATURE_SET_VERSION)

    profile_id = data["profile_id"]
    if not isinstance(profile_id, str) or not PROFILE_ID_PATTERN.fullmatch(profile_id):
        raise ValueError("profile_id must be a lowercase stable identifier")
    display_name = data["display_name"]
    if not isinstance(display_name, str) or not display_name.strip() or display_name != display_name.strip() or len(display_name) > 100:
        raise ValueError("display_name must be 1-100 trimmed characters")
    created_at = data["created_at"]
    if not isinstance(created_at, str):
        raise ValueError("created_at must be an ISO-8601 string")
    try:
        timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("created_at must be a valid ISO-8601 timestamp") from error
    if timestamp.tzinfo is None:
        raise ValueError("created_at must include a timezone")

    provenance_data = _exact_keys(data["provenance"], {"source", "games", "positions", "notes"}, "provenance")
    source = provenance_data["source"]
    if source not in SOURCES:
        raise ValueError(f"unsupported provenance source: {source!r}")
    games = _integer(provenance_data["games"], "provenance.games", 0, 10_000_000)
    positions = _integer(provenance_data["positions"], "provenance.positions", 0, 1_000_000_000)
    notes = provenance_data["notes"]
    if not isinstance(notes, str) or len(notes) > 500:
        raise ValueError("provenance.notes must be at most 500 characters")
    if source == "neutral" and (games != 0 or positions != 0):
        raise ValueError("neutral profiles cannot claim analyzed samples")

    expected_features = set(FEATURE_NAMES)
    weights_data = _exact_keys(data["feature_weights"], expected_features, "feature_weights")
    confidence_data = _exact_keys(data["feature_confidence"], expected_features, "feature_confidence")
    weights = tuple((name, _integer(weights_data[name], f"feature_weights.{name}", -1000, 1000)) for name in FEATURE_NAMES)
    confidence = tuple((name, _integer(confidence_data[name], f"feature_confidence.{name}", 0, 1000)) for name in FEATURE_NAMES)
    if source == "neutral" and (any(value for _, value in weights) or any(value for _, value in confidence)):
        raise ValueError("neutral profiles must have zero weights and confidence")

    return OpponentProfile(
        profile_id=profile_id,
        display_name=display_name,
        created_at=created_at,
        provenance=ProfileProvenance(source, games, positions, notes),
        feature_weights=weights,
        feature_confidence=confidence,
    )


def load_profile(path: str | Path) -> OpponentProfile:
    try:
        text = Path(path).read_text(encoding="utf-8")
        value = json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read opponent profile: {error}") from error
    return profile_from_dict(value)


def dump_profile(profile: OpponentProfile, path: str | Path) -> None:
    # Validation before writing ensures manually constructed instances cannot
    # bypass the external contract.
    validated = profile_from_dict(profile.to_dict())
    Path(path).write_text(json.dumps(validated.to_dict(), indent=2) + "\n", encoding="utf-8")

