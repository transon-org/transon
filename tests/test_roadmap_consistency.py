"""CI guard: every roadmap must track item status consistently everywhere.

This is the deterministic counterpart to the "check every place where we track
status" review step — see ``scripts/check_roadmap.py`` for the rules enforced and
``ROADMAPS`` for the files guarded (engine ``docs/ROADMAP.md`` and docs-site
``docs/DOCS_SITE_ROADMAP.md``).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_roadmap import ROADMAPS, check_spec  # noqa: E402


@pytest.mark.parametrize("spec", ROADMAPS, ids=[spec.rel for spec in ROADMAPS])
def test_roadmap_status_tracking_is_consistent(spec):
    problems = check_spec(spec, ROOT)
    assert not problems, f"{spec.rel} status inconsistencies:\n" + "\n".join(
        f"  - {p}" for p in problems
    )
