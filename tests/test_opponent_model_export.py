import tempfile
import unittest
from pathlib import Path

from tools.export_opponent_error_models import model_source


ROOT = Path(__file__).resolve().parents[1]


class OpponentModelExportTests(unittest.TestCase):
    def test_export_contains_all_trees_and_provenance(self):
        path = ROOT / "models" / "YashDutt7_100k" / "history_strategies" / "lifetime_personal.joblib"
        if not path.exists():
            self.skipTest("local fitted model artifact is unavailable")
        source, metadata = model_source("fixture", path)
        self.assertEqual(metadata["trees"], 300)
        self.assertEqual(metadata["nodes"], 3900)
        self.assertEqual(len(metadata["sha256"]), 64)
        self.assertIn("fixture_model", source)


if __name__ == "__main__":
    unittest.main()
