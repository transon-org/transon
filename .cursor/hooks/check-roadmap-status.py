#!/usr/bin/env python3
"""`stop` hook: nudge the agent to fix ROADMAP status drift before finishing.

Why a ``stop`` hook and not ``afterFileEdit``? Only ``stop`` (and ``subagentStop``)
can return a ``followup_message`` that Cursor auto-submits to the agent — that is
what closes the "please re-check all the status places" loop automatically.
``afterFileEdit`` has no agent-facing output channel.

To stay quiet during unrelated work, this only speaks up when ``docs/ROADMAP.md``
has uncommitted local changes *and* the consistency checker finds a problem. The
``loop_limit`` in ``hooks.json`` caps how many times it can re-prompt.
"""
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
ROADMAP_REL = "docs/ROADMAP.md"


def roadmap_is_dirty() -> bool:
    """True if docs/ROADMAP.md has uncommitted changes (so the agent touched it)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", ROADMAP_REL],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return True  # can't tell -> err on the side of checking
    return bool(result.stdout.strip())


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    if payload.get("status") not in (None, "completed"):
        print("{}")
        return 0

    if not roadmap_is_dirty():
        print("{}")
        return 0

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    try:
        from check_roadmap import check_files
    except ImportError:
        print("{}")
        return 0

    problems = check_files(
        PROJECT_DIR / "docs" / "ROADMAP.md",
        PROJECT_DIR / "CHANGELOG.md",
    )
    if not problems:
        print("{}")
        return 0

    details = "\n".join(f"  - {p}" for p in problems)
    followup = (
        "docs/ROADMAP.md has status-tracking inconsistencies — every item must "
        "carry the same status in the checklist table, its `### R-xx.` section "
        "header, any inline `~~R-xx~~` mention, and CHANGELOG references. Fix "
        "these, then re-run `python scripts/check_roadmap.py`:\n"
        f"{details}"
    )
    print(json.dumps({"followup_message": followup}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
