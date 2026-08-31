import unittest
from pathlib import Path

from engine.adaptive_profile import FEATURE_NAMES, load_profile
from engine.synthetic_profiles import SYNTHETIC_PROFILE_SPECS, synthetic_profiles


ROOT = Path(__file__).resolve().parents[1]


class SyntheticProfileTests(unittest.TestCase):
    def test_checked_in_profiles_match_deterministic_definitions(self):
        generated = synthetic_profiles()
        self.assertEqual(len(generated), 4)
        for profile in generated:
            stored = load_profile(ROOT / "profiles" / "synthetic" / f"{profile.profile_id}.json")
            self.assertEqual(stored, profile)

    def test_profiles_are_distinct_complete_and_bounded(self):
        profiles = synthetic_profiles()
        self.assertEqual(len({profile.profile_id for profile in profiles}), len(profiles))
        vectors = {profile.feature_weights for profile in profiles}
        self.assertEqual(len(vectors), len(profiles))
        for profile in profiles:
            weights = dict(profile.feature_weights)
            confidence = dict(profile.feature_confidence)
            self.assertEqual(tuple(weights), FEATURE_NAMES)
            self.assertTrue(any(weights.values()))
            self.assertTrue(all(-1000 <= value <= 1000 for value in weights.values()))
            self.assertTrue(all(confidence[name] == (1000 if weights[name] else 0) for name in FEATURE_NAMES))
            self.assertEqual(profile.provenance.source, "synthetic")
            self.assertEqual(profile.provenance.games, 0)

    def test_archetypes_encode_their_declared_direction(self):
        profiles = {profile.profile_id: profile for profile in synthetic_profiles()}
        tactical = profiles["synthetic-tactical-pressure-v1"]
        simplification = profiles["synthetic-simplification-pressure-v1"]
        complexity = profiles["synthetic-complexity-pressure-v1"]
        positional = profiles["synthetic-positional-restriction-v1"]
        self.assertGreater(tactical.weight("gives_check"), 0)
        self.assertLess(tactical.weight("legal_reply_count"), 0)
        self.assertLess(simplification.weight("remaining_non_pawn_material_cp"), 0)
        self.assertGreater(complexity.weight("remaining_non_pawn_material_cp"), 0)
        self.assertGreater(complexity.weight("pawn_tension_count"), 0)
        self.assertGreater(positional.weight("center_control_balance"), 0)
        self.assertGreater(positional.weight("mobility_balance"), 0)

    def test_spec_ids_are_stable_and_versioned(self):
        for spec in SYNTHETIC_PROFILE_SPECS:
            self.assertTrue(spec.profile_id.endswith("-v1"))


if __name__ == "__main__":
    unittest.main()
