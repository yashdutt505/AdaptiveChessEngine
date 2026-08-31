import json
import tempfile
import unittest
from pathlib import Path

from engine.adaptive_profile import FEATURE_NAMES, dump_profile, load_profile, profile_from_dict


ROOT = Path(__file__).resolve().parents[1]


class AdaptiveProfileTests(unittest.TestCase):
    def setUp(self):
        self.neutral_path = ROOT / "profiles" / "neutral_v1.json"
        self.data = json.loads(self.neutral_path.read_text(encoding="utf-8"))

    def test_canonical_neutral_profile_loads_and_is_complete(self):
        profile = load_profile(self.neutral_path)
        self.assertEqual(profile.schema_version, 1)
        self.assertEqual(tuple(dict(profile.feature_weights)), FEATURE_NAMES)
        self.assertTrue(all(profile.weight(name) == 0 for name in FEATURE_NAMES))
        self.assertTrue(all(profile.confidence(name) == 0 for name in FEATURE_NAMES))

    def test_round_trip_is_stable(self):
        profile = load_profile(self.neutral_path)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "profile.json"
            dump_profile(profile, output)
            self.assertEqual(load_profile(output), profile)

    def test_non_neutral_profile_accepts_bounded_preferences_and_confidence(self):
        candidate = json.loads(json.dumps(self.data))
        candidate["profile_id"] = "synthetic-tactical-v1"
        candidate["display_name"] = "Synthetic tactical profile"
        candidate["provenance"] = {"source": "synthetic", "games": 0, "positions": 24, "notes": "Test fixture"}
        candidate["feature_weights"]["gives_check"] = 750
        candidate["feature_confidence"]["gives_check"] = 1000
        profile = profile_from_dict(candidate)
        self.assertEqual(profile.weight("gives_check"), 750)
        self.assertEqual(profile.confidence("gives_check"), 1000)

    def test_rejects_unknown_missing_and_unsupported_versions(self):
        unknown = dict(self.data, surprise=True)
        with self.assertRaisesRegex(ValueError, "unknown"):
            profile_from_dict(unknown)
        missing = dict(self.data)
        del missing["profile_id"]
        with self.assertRaisesRegex(ValueError, "missing"):
            profile_from_dict(missing)
        unsupported = dict(self.data, schema_version=2)
        with self.assertRaises(ValueError):
            profile_from_dict(unsupported)

    def test_rejects_incomplete_and_out_of_range_feature_data(self):
        incomplete = json.loads(json.dumps(self.data))
        del incomplete["feature_weights"]["gives_check"]
        with self.assertRaisesRegex(ValueError, "missing"):
            profile_from_dict(incomplete)
        excessive = json.loads(json.dumps(self.data))
        excessive["feature_weights"]["gives_check"] = 1001
        with self.assertRaises(ValueError):
            profile_from_dict(excessive)
        wrong_type = json.loads(json.dumps(self.data))
        wrong_type["feature_confidence"]["gives_check"] = True
        with self.assertRaises(ValueError):
            profile_from_dict(wrong_type)

    def test_neutral_profile_cannot_claim_effect_or_samples(self):
        weighted = json.loads(json.dumps(self.data))
        weighted["feature_weights"]["gives_check"] = 1
        with self.assertRaisesRegex(ValueError, "neutral"):
            profile_from_dict(weighted)
        sampled = json.loads(json.dumps(self.data))
        sampled["provenance"]["games"] = 1
        with self.assertRaisesRegex(ValueError, "neutral"):
            profile_from_dict(sampled)

    def test_json_loader_rejects_duplicate_and_non_finite_values(self):
        with tempfile.TemporaryDirectory() as directory:
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"schema": "a", "schema": "b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_profile(duplicate)
            invalid = Path(directory) / "nan.json"
            invalid.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non-finite"):
                load_profile(invalid)


if __name__ == "__main__":
    unittest.main()
