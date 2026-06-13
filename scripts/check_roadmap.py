#!/usr/bin/env python3
"""Validate status-tracking consistency in the project's roadmap files.

Two roadmaps are tracked, each with its own item-ID prefix:

- ``docs/ROADMAP.md`` — engine semantics, IDs ``R-xx`` (cross-checked against
  ``CHANGELOG.md`` references like ``(Roadmap R-01, option 1)``).
- ``docs/DOCS_SITE_ROADMAP.md`` — docs-site / playground content, IDs ``D-xx``
  (no changelog cross-check: content items are not tracked in ``CHANGELOG.md``).

Each roadmap records every item's status in several places that must stay aligned:

1. the **Checklist** table (the ``Status`` column),
2. each item's ``**Status**:`` header line,
3. inline strikethrough mentions like ``~~R-01~~ (done)``,
4. (engine roadmap only) ``CHANGELOG.md`` references like ``(Roadmap R-01, option 1)``.

The whole point of this list is that *once an item carries a status, it carries it
everywhere*. A "mixed" state — present in the table but not the section, struck
through while still ``needs-decision``, shipped in the changelog but still
``accepted`` — is exactly the drift this checker catches.

Run it three ways:
  - directly: ``python scripts/check_roadmap.py`` (checks every roadmap; exit 1 on any
    problem). Pass a single file path to check just that one;
  - from pytest: ``tests/test_roadmap_consistency.py`` (blocks CI; parametrized over
    every roadmap);
  - from the ``stop`` hook: ``.cursor/hooks/check-roadmap-status.py`` (nudges the
    agent to self-correct before the human ever has to ask).

Pure stdlib, Python 3.9+, no project imports — safe to run in any environment.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple

#: Allowed status vocabulary, declared once in each roadmap's "Statuses" legend.
STATUSES = ("needs-decision", "accepted", "in-progress", "done", "rejected")

#: A struck-through item is, by convention, resolved.
RESOLVED = {"done", "rejected"}

#: A changelog reference means the change shipped (or is shipping).
SHIPPED = {"done", "in-progress"}

#: Default item-ID prefix when none is supplied or detectable.
DEFAULT_PREFIX = "R"

_STATUS_TOKEN = re.compile(
    r"(?<![\w-])(" + "|".join(STATUSES) + r")(?![\w-])"
)
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
#: Detect the item-ID prefix from the first ``### <PREFIX>-NN.`` section header.
_ANY_SECTION_HEADER = re.compile(r"^###\s+([A-Za-z]+)-\d{2,}\.", re.MULTILINE)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHANGELOG = PROJECT_ROOT / "CHANGELOG.md"


class _Patterns(NamedTuple):
    item_id: re.Pattern
    section_header: re.Pattern
    strikethrough: re.Pattern
    changelog_ref: re.Pattern


class RoadmapSpec(NamedTuple):
    """A roadmap file the checker knows how to validate."""

    rel: str                       # path relative to the repo root
    changelog_rel: Optional[str]   # changelog to cross-check, or None
    id_prefix: str                 # item-ID prefix (e.g. "R", "D")


#: Every roadmap guarded by this checker. Add new roadmaps here.
ROADMAPS: Tuple[RoadmapSpec, ...] = (
    RoadmapSpec("docs/ROADMAP.md", "CHANGELOG.md", "R"),
    RoadmapSpec("docs/DOCS_SITE_ROADMAP.md", None, "D"),
)


def _build_patterns(prefix: str) -> _Patterns:
    p = re.escape(prefix)
    return _Patterns(
        item_id=re.compile(rf"{p}-\d{{2,}}"),
        section_header=re.compile(rf"^###\s+({p}-\d{{2,}})\.", re.MULTILINE),
        strikethrough=re.compile(rf"~~\s*({p}-\d{{2,}})\s*~~"),
        changelog_ref=re.compile(rf"Roadmap\s+({p}-\d{{2,}})"),
    )


def _detect_prefix(text: str, default: str = DEFAULT_PREFIX) -> str:
    match = _ANY_SECTION_HEADER.search(text)
    return match.group(1) if match else default


def _first_status(text: str) -> Optional[str]:
    match = _STATUS_TOKEN.search(text)
    return match.group(1) if match else None


def parse_table(text: str, patterns: _Patterns) -> tuple:
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
        id_match = patterns.item_id.search(cells[0])
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


def parse_sections(text: str, patterns: _Patterns) -> tuple:
    """Map item id -> status from each ``### <id>.`` section header block."""
    statuses: dict = {}
    problems: List[str] = []
    headers = list(patterns.section_header.finditer(text))
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


def parse_strikethroughs(text: str, patterns: _Patterns) -> List[Tuple[str, Optional[str]]]:
    """Find ``~~<id>~~`` mentions and any status keyword within the next ~24 chars."""
    found: List[Tuple[str, Optional[str]]] = []
    for match in patterns.strikethrough.finditer(text):
        window = text[match.end():match.end() + 24]
        found.append((match.group(1), _first_status(window)))
    return found


def parse_changelog_refs(text: str, patterns: _Patterns) -> List[str]:
    return patterns.changelog_ref.findall(text)


def check(
    roadmap_text: str,
    changelog_text: Optional[str] = None,
    *,
    id_prefix: Optional[str] = None,
) -> List[str]:
    """Return a list of human-readable consistency problems (empty == all good).

    ``id_prefix`` selects the item-ID family (``"R"``/``"D"``/…); when ``None`` it is
    auto-detected from the first ``### <PREFIX>-NN.`` section header.
    """
    prefix = id_prefix or _detect_prefix(roadmap_text)
    patterns = _build_patterns(prefix)
    problems: List[str] = []

    table, table_problems = parse_table(roadmap_text, patterns)
    sections, section_problems = parse_sections(roadmap_text, patterns)
    problems.extend(table_problems)
    problems.extend(section_problems)

    if not table:
        problems.append(
            f"no {prefix}-NN checklist table rows found — is the table present?"
        )

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
    for item, inline_status in parse_strikethroughs(roadmap_text, patterns):
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
        for item in sorted(set(parse_changelog_refs(changelog_text, patterns))):
            if item not in table:
                problems.append(f"CHANGELOG references {item}, which is not in the roadmap table")
            elif table[item] is not None and table[item] not in SHIPPED:
                problems.append(
                    f"CHANGELOG references {item} as shipped, but its roadmap status is {table[item]!r}"
                )

    return problems


def check_files(
    roadmap_path: Path,
    changelog_path: Optional[Path] = DEFAULT_CHANGELOG,
    *,
    id_prefix: Optional[str] = None,
) -> List[str]:
    roadmap_path = Path(roadmap_path)
    if not roadmap_path.exists():
        return [f"roadmap file not found: {roadmap_path}"]
    changelog_text = None
    if changelog_path is not None and Path(changelog_path).exists():
        changelog_text = Path(changelog_path).read_text(encoding="utf-8")
    return check(
        roadmap_path.read_text(encoding="utf-8"),
        changelog_text,
        id_prefix=id_prefix,
    )


def check_spec(spec: RoadmapSpec, root: Path = PROJECT_ROOT) -> List[str]:
    """Run the checker for a registered :class:`RoadmapSpec`."""
    changelog = root / spec.changelog_rel if spec.changelog_rel else None
    return check_files(root / spec.rel, changelog, id_prefix=spec.id_prefix)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv:
        # Single-file mode: explicit roadmap (+ optional changelog). Prefix is
        # auto-detected from the file's section headers.
        roadmap = Path(argv[0])
        changelog = Path(argv[1]) if len(argv) >= 2 else None
        runs = [(str(roadmap), check_files(roadmap, changelog))]
    else:
        runs = [(spec.rel, check_spec(spec)) for spec in ROADMAPS]

    total = 0
    for label, problems in runs:
        if problems:
            total += len(problems)
            print(f"{label}: status inconsistencies ({len(problems)}):")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"{label}: status tracking is consistent.")

    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
