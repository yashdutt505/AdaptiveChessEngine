"""Deterministic synthetic profiles for adaptive-layer experiments."""

from __future__ import annotations

from dataclasses import dataclass

from engine.adaptive_profile import FEATURE_NAMES, OpponentProfile, ProfileProvenance, profile_from_dict


@dataclass(frozen=True, slots=True)
class SyntheticProfileSpec:
    profile_id: str
    display_name: str
    notes: str
    weights: dict[str, int]


SYNTHETIC_PROFILE_SPECS = (
    SyntheticProfileSpec(
        "synthetic-tactical-pressure-v1",
        "Synthetic tactical pressure",
        "Experimental policy that seeks forcing, open, materially imbalanced positions with fewer opponent replies.",
        {
            "capture_value_cp": 650,
            "promotion_gain_cp": 400,
            "gives_check": 900,
            "legal_reply_count": -500,
            "material_imbalance_cp": 450,
            "remaining_non_pawn_material_cp": 250,
            "open_file_count": 350,
            "center_control_balance": 300,
            "pawn_tension_count": 250,
            "irreversible": 200,
        },
    ),
    SyntheticProfileSpec(
        "synthetic-simplification-pressure-v1",
        "Synthetic simplification pressure",
        "Experimental policy that seeks exchanges, reduced material, low tension, and safe conversion positions.",
        {
            "capture_value_cp": 700,
            "legal_reply_count": -150,
            "material_balance_cp": 500,
            "material_imbalance_cp": -250,
            "remaining_non_pawn_material_cp": -900,
            "remaining_pawn_count": -350,
            "king_safety_balance": 400,
            "pawn_tension_count": -500,
            "irreversible": 300,
        },
    ),
    SyntheticProfileSpec(
        "synthetic-complexity-pressure-v1",
        "Synthetic complexity pressure",
        "Experimental policy that preserves pieces and choices while increasing tension, imbalance, and commitment.",
        {
            "legal_reply_count": 450,
            "material_imbalance_cp": 600,
            "remaining_non_pawn_material_cp": 850,
            "remaining_pawn_count": 300,
            "open_file_count": 250,
            "mobility_balance": 350,
            "pawn_tension_count": 750,
            "irreversible": 450,
        },
    ),
    SyntheticProfileSpec(
        "synthetic-positional-restriction-v1",
        "Synthetic positional restriction",
        "Experimental policy that emphasizes mobility, king safety, pawn structure, center control, and restricted replies.",
        {
            "legal_reply_count": -550,
            "material_balance_cp": 250,
            "mobility_balance": 800,
            "king_safety_balance": 650,
            "pawn_structure_balance": 700,
            "center_control_balance": 850,
            "pawn_tension_count": -200,
            "castles": 350,
        },
    ),
)


def build_synthetic_profile(spec: SyntheticProfileSpec) -> OpponentProfile:
    unknown = set(spec.weights) - set(FEATURE_NAMES)
    if unknown:
        raise ValueError(f"unknown synthetic profile features: {sorted(unknown)}")
    weights = {name: spec.weights.get(name, 0) for name in FEATURE_NAMES}
    confidence = {name: 1000 if weights[name] else 0 for name in FEATURE_NAMES}
    return profile_from_dict(
        {
            "schema": "ace.opponent-profile",
            "schema_version": 1,
            "feature_set_version": 1,
            "profile_id": spec.profile_id,
            "display_name": spec.display_name,
            "created_at": "2026-08-31T00:00:00+05:30",
            "provenance": {
                "source": "synthetic",
                "games": 0,
                "positions": 0,
                "notes": spec.notes,
            },
            "feature_weights": weights,
            "feature_confidence": confidence,
        }
    )


def synthetic_profiles() -> tuple[OpponentProfile, ...]:
    return tuple(build_synthetic_profile(spec) for spec in SYNTHETIC_PROFILE_SPECS)

