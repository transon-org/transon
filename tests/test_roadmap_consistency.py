"""CI guard: ``docs/ROADMAP.md`` must track item status consistently everywhere.

This is the deterministic counterpart to the "check every place where we track
status" review step — see ``scripts/check_roadmap.py`` for the rules enforced.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_roadmap import check_files  # noqa: E402


def test_roadmap_status_tracking_is_consistent():
    problems = check_files(ROOT / "docs" / "ROADMAP.md", ROOT / "CHANGELOG.md")
    assert not problems, "ROADMAP status inconsistencies:\n" + "\n".join(
        f"  - {p}" for p in problems
    )
