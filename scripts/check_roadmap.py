#!/usr/bin/env python3
"""Validate status-tracking consistency in ``docs/ROADMAP.md``.

The roadmap records each item's status in several places that must stay aligned —
the recurring "did we update the status everywhere?" question, made mechanical:

1. the **Checklist** table (the ``Status`` column),
2. each item's ``**Status**:`` header line,
3. inline strikethrough mentions like ``~~R-01~~ (done)``,
4. ``CHANGELOG.md`` references like ``(Roadmap R-01, option 1)``.

The whole point of this list is that *once an item carries a status, it carries it
everywhere*. A "mixed" state — present in the table but not the section, struck
through while still ``needs-decision``, shipped in the changelog but still
``accepted`` — is exactly the drift this checker catches.

Run it three ways:
  - directly: ``python scripts/check_roadmap.py`` (exit 1 on any problem);
  - from pytest: ``tests/test_roadmap_consistency.py`` (blocks CI);
  - from the ``stop`` hook: ``.cursor/hooks/check-roadmap-status.py`` (nudges the
    agent to self-correct before the human ever has to ask).

Pure stdlib, Python 3.9+, no project imports — safe to run in any environment.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

#: Allowed status vocabulary, declared once in ROADMAP.md's "Statuses" legend.
STATUSES = ("needs-decision", "accepted", "in-progress", "done", "rejected")

#: A struck-through item is, by convention, resolved.
RESOLVED = {"done", "rejected"}

#: A changelog reference means the change shipped (or is shipping).
SHIPPED = {"done", "in-progress"}

_STATUS_TOKEN = re.compile(
    r"(?<![\w-])(" + "|".join(STATUSES) + r")(?![\w-])"
)
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_ITEM_ID = re.compile(r"R-\d{2,}")
_SECTION_HEADER = re.compile(r"^###\s+(R-\d{2,})\.", re.MULTILINE)
_STRIKETHROUGH = re.compile(r"~~\s*(R-\d{2,})\s*~~")
_CHANGELOG_REF = re.compile(r"Roadmap\s+(R-\d{2,})")

DEFAULT_ROADMAP = Path(__file__).resolve().parent.parent / "docs" / "ROADMAP.md"
DEFAULT_CHANGELOG = Path(__file__).resolve().parent.parent / "CHANGELOG.md"


def _first_status(text: str) -> Optional[str]:
    match = _STATUS_TOKEN.search(text)
    return match.group(1) if match else None


def parse_table(text: str) -> dict:
    """Map item id -> status from the Checklist table, plus malformed-row notes.

    Returns ``(statuses, problems)``. A row whose status cell is empty or outside
    the vocabulary is reported but still recorded (as ``None``) so downstream
    cross-checks can flag the mismatch too.
    """
    statuses: dict = {}
    problems: List[str] = []
    for raw in text.splitlines():
        if not _TABLE_ROW.match(raw):
            continue
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        if not cells:
            continue
        id_match = _ITEM_ID.search(cells[0])
        if not id_match:
            continue  # header, separator, or a non-item row
        item = id_match.group(0)
        status_cell = cells[-1] if len(cells) > 1 else ""
        if item in statuses:
            problems.append(f"{item}: appears more than once in the checklist table")
        if not status_cell:
            problems.append(f"{item}: checklist table row has an empty Status cell")
            statuses[item] = None
        elif status_cell not in STATUSES:
            problems.append(
                f"{item}: checklist table status {status_cell!r} is not one of "
                + ", ".join(STATUSES)
            )
            statuses[item] = None
        else:
            statuses[item] = status_cell
    return statuses, problems


def parse_sections(text: str) -> dict:
    """Map item id -> status from each ``### R-xx.`` section header block."""
    statuses: dict = {}
    problems: List[str] = []
    headers = list(_SECTION_HEADER.finditer(text))
    for index, header in enumerate(headers):
        item = header.group(1)
        start = header.end()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        body = text[start:end]
        status_label = re.search(r"\*\*Status\*\*:\s*(.*?)(?:·|\n\n|$)", body, re.DOTALL)
        if not status_label:
            problems.append(f"{item}: section has no parseable `**Status**:` line")
            statuses[item] = None
            continue
        status = _first_status(status_label.group(1))
        if status is None:
            problems.append(
                f"{item}: section `**Status**:` line has no recognized status keyword"
            )
        statuses[item] = status
    return statuses, problems


def parse_strikethroughs(text: str) -> List[Tuple[str, Optional[str]]]:
    """Find ``~~R-xx~~`` mentions and any status keyword within the next ~24 chars."""
    found: List[Tuple[str, Optional[str]]] = []
    for match in _STRIKETHROUGH.finditer(text):
        window = text[match.end():match.end() + 24]
        found.append((match.group(1), _first_status(window)))
    return found


def parse_changelog_refs(text: str) -> List[str]:
    return _CHANGELOG_REF.findall(text)


def check(roadmap_text: str, changelog_text: Optional[str] = None) -> List[str]:
    """Return a list of human-readable consistency problems (empty == all good)."""
    problems: List[str] = []

    table, table_problems = parse_table(roadmap_text)
    sections, section_problems = parse_sections(roadmap_text)
    problems.extend(table_problems)
    problems.extend(section_problems)

    if not table:
        problems.append("no checklist table rows found — is the table present?")

    # Table <-> section coverage and agreement.
    for item in sorted(set(table) - set(sections)):
        problems.append(f"{item}: in the checklist table but has no `### {item}.` section")
    for item in sorted(set(sections) - set(table)):
        problems.append(f"{item}: has a `### {item}.` section but is missing from the checklist table")
    for item in sorted(set(table) & set(sections)):
        t_status, s_status = table[item], sections[item]
        if t_status is not None and s_status is not None and t_status != s_status:
            problems.append(
                f"{item}: checklist table says {t_status!r} but the section header says {s_status!r}"
            )

    # Inline strikethrough mentions must reference resolved items consistently.
    for item, inline_status in parse_strikethroughs(roadmap_text):
        if item not in table:
            problems.append(f"~~{item}~~ is struck through but {item} is not in the checklist table")
            continue
        table_status = table[item]
        if table_status is not None and table_status not in RESOLVED:
            problems.append(
                f"~~{item}~~ is struck through (implies resolved) but its status is {table_status!r}"
            )
        if inline_status is not None and table_status is not None and inline_status != table_status:
            problems.append(
                f"inline ~~{item}~~ ({inline_status}) disagrees with the checklist status {table_status!r}"
            )

    # Changelog references imply the item shipped.
    if changelog_text is not None:
        for item in sorted(set(parse_changelog_refs(changelog_text))):
            if item not in table:
                problems.append(f"CHANGELOG references {item}, which is not in the roadmap table")
            elif table[item] is not None and table[item] not in SHIPPED:
                problems.append(
                    f"CHANGELOG references {item} as shipped, but its roadmap status is {table[item]!r}"
                )

    return problems


def check_files(
    roadmap_path: Path = DEFAULT_ROADMAP,
    changelog_path: Optional[Path] = DEFAULT_CHANGELOG,
) -> List[str]:
    roadmap_path = Path(roadmap_path)
    if not roadmap_path.exists():
        return [f"roadmap file not found: {roadmap_path}"]
    changelog_text = None
    if changelog_path is not None and Path(changelog_path).exists():
        changelog_text = Path(changelog_path).read_text(encoding="utf-8")
    return check(roadmap_path.read_text(encoding="utf-8"), changelog_text)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    roadmap = Path(argv[0]) if len(argv) >= 1 else DEFAULT_ROADMAP
    changelog = Path(argv[1]) if len(argv) >= 2 else DEFAULT_CHANGELOG
    problems = check_files(roadmap, changelog)
    if problems:
        print(f"ROADMAP status inconsistencies ({len(problems)}):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("ROADMAP status tracking is consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
