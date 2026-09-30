import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tools.create_blinded_match_schedule import ARMS, create_schedule, validate_openings


class BlindedScheduleTests(unittest.TestCase):
    def test_openings_are_legal(self):
        validate_openings()

    def test_confirmatory_blocks_balance_arm_and_color(self):
        schedule = create_schedule(1234)
        confirmatory = [item for item in schedule["sessions"] if item["phase"] == "confirmatory"]
        self.assertEqual(len(confirmatory), 160)
        for block in range(1, 21):
            entries = [item for item in confirmatory if item["block"] == block]
            self.assertEqual(Counter((item["arm"], item["player_color"]) for item in entries),
                             Counter((arm, color) for arm in ARMS for color in ("white", "black")))
            self.assertEqual(len({tuple(item["opening_moves"]) for item in entries}), 1)

    def test_schedule_serialization_has_stable_commitment(self):
        schedule = create_schedule(5)
        text = json.dumps(schedule, indent=2) + "\n"
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
