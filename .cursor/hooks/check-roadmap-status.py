#!/usr/bin/env python3
"""`stop` hook: nudge the agent to fix roadmap status drift before finishing.

Why a ``stop`` hook and not ``afterFileEdit``? Only ``stop`` (and ``subagentStop``)
can return a ``followup_message`` that Cursor auto-submits to the agent — that is
what closes the "please re-check all the status places" loop automatically.
``afterFileEdit`` has no agent-facing output channel.

To stay quiet during unrelated work, this only speaks up about a roadmap that has
uncommitted local changes *and* fails the consistency checker. The set of roadmaps
guarded comes from ``check_roadmap.ROADMAPS`` (engine ``docs/ROADMAP.md`` and
docs-site ``docs/DOCS_SITE_ROADMAP.md``), so it stays in sync automatically. The
``loop_limit`` in ``hooks.json`` caps how many times it can re-prompt.
"""
import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


def file_is_dirty(rel_path: str) -> bool:
    """True if ``rel_path`` has uncommitted changes (so the agent touched it)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", rel_path],
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

    sys.path.insert(0, str(PROJECT_DIR / "scripts"))
    try:
        from check_roadmap import ROADMAPS, check_spec
    except ImportError:
        print("{}")
        return 0

    sections: list = []
    for spec in ROADMAPS:
        if not file_is_dirty(spec.rel):
            continue
        problems = check_spec(spec, PROJECT_DIR)
        if not problems:
            continue
        details = "\n".join(f"  - {p}" for p in problems)
        sections.append(f"{spec.rel}:\n{details}")

    if not sections:
        print("{}")
        return 0

    followup = (
        "A roadmap has status-tracking inconsistencies — every item must carry the "
        "same status in the checklist table, its `### <id>.` section header, any "
        "inline `~~<id>~~` mention, and (for the engine roadmap) CHANGELOG "
        "references. Fix these, then re-run `python scripts/check_roadmap.py`:\n"
        + "\n".join(sections)
    )
    print(json.dumps({"followup_message": followup}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
