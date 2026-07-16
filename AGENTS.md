# AGENTS.md — transon engine

Homogeneous JSON-to-JSON template engine: `Transformer(template).transform(data)`.
This file is the canonical, tool-neutral operating contract for agents working in this repo.

**The engine contract is [`docs/SPECIFICATION.md`](docs/SPECIFICATION.md)** — read the relevant
section before any non-trivial change. The improvement backlog and open design questions live
**only** in [`docs/ROADMAP.md`](docs/ROADMAP.md) (engine semantics, `R-xx`) and
[`docs/DOCS_SITE_ROADMAP.md`](docs/DOCS_SITE_ROADMAP.md) (docs-site content, `D-xx`).

## Harness — read before working

The AI-development setup (rules, commands, hooks, gates, skills, MCP recommendations) is
described in [`docs/AI_DEVELOPMENT.md`](docs/AI_DEVELOPMENT.md) — **read it first**; it is the
authoritative map of the harness. The harness itself lives in [`.cursor/`](.cursor/) and is
binding for every agent, not just Cursor:

- **Rules** (`.cursor/rules/`) — canonical project guidance. Cursor auto-applies them by glob;
  any other tool must load them manually by scope:
  - `transon-overview.mdc` — always: architecture map + invariants. Apply to every session.
  - `adding-rules.mdc` — when touching `transon/*.py` (rules/operators/functions).
  - `testing-conventions.mdc` — when touching `transon/tests/*.py` or `tests/*.py`.
  - `status-consistency.mdc` — when touching `docs/ROADMAP.md` or `CHANGELOG.md`.
- **Commands** (`.cursor/commands/`) — the per-item workflows. Follow them verbatim even when
  invoked outside Cursor: `fix-roadmap-item.md` (engine `R-xx`), `fix-docs-item.md`
  (content `D-xx`).
- **Deterministic gate** — `python scripts/check_roadmap.py` must print "consistent" after any
  edit to `docs/ROADMAP.md`, `docs/DOCS_SITE_ROADMAP.md`, or `CHANGELOG.md`. The same check runs
  in CI (`tests/test_roadmap_consistency.py`) and as a Cursor `stop` hook
  (`.cursor/hooks/check-roadmap-status.py`); a red gate is a STOP — fix it, never bypass it.
- **Skills** (`.agents/skills/`) — installed, not committed: run `./scripts/install-skills.sh`
  once per clone; the pinned manifest is `scripts/skills-manifest.txt`.

## Golden rules (invariants — do not break)

1. Templates are pure JSON; a dict containing the marker key (default `"$"`) is a rule
   invocation, everything else is copied literally. **No string-embedded DSLs.**
2. Rule parameters are templates themselves — evaluate dynamic params with `t.walk()`.
3. `t.NO_CONTENT` is the "no value" sentinel: produced by `attr`/`get` misses, skipped by
   `map`/`object`/`file`/`filter`. Preserve these skipping semantics.
4. `DefinitionError` = malformed template; `TransformationError` = incompatible data.
5. Registries (`_rules`, `_operators`, `_functions`) are MRO-resolved; subclassing `Transformer`
   resets them, so subclass registrations never affect the base class.
6. `transform()` must never mutate the input data or the template.
7. Python 3.9+ compatible (CI matrix 3.9–3.13), **stdlib only** — no new runtime dependencies.
8. **Never change behavior silently.** Engine-semantics changes need a recorded decision in
   `docs/ROADMAP.md`, spec text updates, and a `CHANGELOG.md` entry when existing templates may
   have relied on the old behavior.

## Map

- `transon/transformers.py` — engine core (`Transformer`, `Context`, `NoContent`, errors)
- `transon/rules.py` — all built-in rules (`@Transformer.register_rule`)
- `transon/operators.py` / `transon/functions.py` — `expr` operators / `call` functions
- `transon/docs.py` — generates docs JSON from docstrings + test corpus
- `transon/tests/` — table-driven example corpus; every case IS a documentation example
- `tests/` — plain pytest for engine mechanics and error paths
- `docs/proposals/` — design proposals (numbered, see its `README.md`)

## Development loop

Docstrings and `register_rule` param kwargs are published documentation; example-corpus cases in
`transon/tests/` are the rendered examples (tagged `"<rule>"` / `"<rule>:<param>"`, never `TBD`).
Before finishing: `pytest .` green (coverage not reduced), `uv run python -m transon.docs`
reports no `TBD`, and `python scripts/check_roadmap.py` prints "consistent".
