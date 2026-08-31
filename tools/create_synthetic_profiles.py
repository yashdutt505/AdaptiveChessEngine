"""Regenerate the checked-in synthetic opponent profile fixtures."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.adaptive_profile import dump_profile  # noqa: E402
from engine.synthetic_profiles import synthetic_profiles  # noqa: E402


OUTPUT = ROOT / "profiles" / "synthetic"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    expected = set()
    for profile in synthetic_profiles():
        path = OUTPUT / f"{profile.profile_id}.json"
        dump_profile(profile, path)
        expected.add(path.name)
    unexpected = sorted(path.name for path in OUTPUT.glob("*.json") if path.name not in expected)
    if unexpected:
        raise RuntimeError(f"unexpected synthetic profile files: {unexpected}")
    print(f"Wrote {len(expected)} synthetic profiles to {OUTPUT}")


if __name__ == "__main__":
    main()
