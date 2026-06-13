# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- `join` returns `NO_CONTENT` when there are no items to join (including when every
  item is `NO_CONTENT`), instead of vacuously producing `""`. Optional dynamic
  `default` supplies a fallback value (same pattern as `attr`/`get`/`format`/`include`).
  (Roadmap R-12, option 1 refined)

  Migration: templates that relied on empty `join` returning `""` must add
  `"default": ""` or compose a fallback (e.g. `chain` + `expr` `or`).

- `NoContent` is falsy in boolean context, so `expr` `and`/`or` treat `NO_CONTENT`
  like a missing value and fall through to the other operand. (Roadmap R-12)

  Migration: templates that passed `NO_CONTENT` through `expr` `or` expecting it to
  be kept must use identity checks elsewhere; use `default` or an explicit fallback
  operand.

- `zip` returns lists of lists instead of Python tuples, so output rows are
  JSON-friendly and work with `join` and numeric `attr` indexing. Any iterable
  item is still accepted (strings zip character-wise, as with Python `zip`).
  (Roadmap R-11, option 2)

  Migration: code that compared output row types to `tuple` or relied on tuple
  semantics must use lists instead; template behavior is otherwise unchanged.

### Added

- `object` rule gained a `fields` mode: `{"$": "object", "fields": {…}}` builds a
  dict from a literal mapping whose keys are emitted verbatim (including the marker
  `$`) and whose values are walked as templates. This is the canonical way to emit
  an object key that is the marker itself — data that would otherwise be read as a
  rule invocation — while keeping values dynamic. Entries whose value evaluates to
  `NO_CONTENT` are omitted. Purely additive; the `key`/`value` mode is unchanged.
  (Roadmap R-14, option 4)

- Opt-in static template validation: `Transformer.validate()` and
  `Transformer(..., validate=True)` raise `DefinitionError` for unknown rules,
  unknown parameters, missing required parameters, ambiguous mutually-exclusive
  parameter combinations, and invalid literal operator/function names. Rule schemas
  are declared via `_required` and `_modes` on `register_rule`. (Roadmap R-04,
  option 1)

- `DefinitionError` and `TransformationError` messages include the template path
  where the failure occurred (dict keys, list indices, rule names, parameter names).
  (Roadmap R-05, option 1)

## [0.0.10] - 2026-06-13

### Fixed

- Release CI: `uv build` failed when `.python-version` pinned an exact patch not
  installed on the runner; use `3.11` and `uv build --python 3.11`.

### Changed

- Published wheel again includes `transon/tests` so `transon.docs` and the docs
  playground can load the example corpus from PyPI.

## [0.0.9] - 2026-06-13

### Added

- Optional dynamic `default` parameter on `attr`, `get`, `format`, and `include` —
  returned instead of `NO_CONTENT` when a lookup, format, or include would otherwise
  produce no value. (Roadmap R-10, option 1)

### Changed

- `transform(data, no_content=None)` — callers choose the substitute when the template
  produces `NO_CONTENT` (`None` by default; pass `Transformer.NO_CONTENT` to receive
  the raw sentinel). (Roadmap R-06, option 2)

  Migration: code that compared `transform(...)` against `Transformer.NO_CONTENT` must
  pass `no_content=Transformer.NO_CONTENT` or check for `None` with the default.

- `format` returns `NO_CONTENT` when the formatting value (or any unpacked list
  element or dict key/value) is `NO_CONTENT`, instead of interpolating the sentinel
  repr into the output string. Use `default` for a fallback. (Roadmap R-07, option 1)

  Migration: templates that accidentally produced garbage strings from missing values
  now get `NO_CONTENT` (mapped to `None` at `transform()` by default); add `default`
  where a substitute string is needed.

- `join` omits `NO_CONTENT` items before concatenation, aligning with `map`/`object`/
  `filter` skip semantics. (Roadmap R-08, option 1)

  Migration: templates that relied on `join` raising when an item was missing now get
  partial joins instead; use explicit validation if raising is required.

- **Python 3.9+ required** — dropped 3.7/3.8 support; removed `importlib-metadata`
  runtime backport and 3.7 compat cursor rules. (Roadmap R-20, option 1)

  Migration: upgrade to Python 3.9 or newer.

- **Poetry → uv** — packaging and CI now use uv (`uv sync --dev`, `uv run pytest`,
  `uv build`). `pyproject.toml` is PEP 621; lockfile is `uv.lock`.

  Migration: install [uv](https://docs.astral.sh/uv/), run `uv sync --dev` instead of
  `poetry install --with dev`.

- CI test matrix: Python 3.9–3.13 via `astral-sh/setup-uv` (replaces Poetry on
  GitHub Actions).

- Packaging: PEP 639 `license = "MIT"`, added `LICENSE` file, tightened hatchling
  sdist includes, pinned `hatchling>=1.27.0`; release workflow uses `setup-uv@v8`.

## [0.0.8] - 2026-06-13

### Changed

- `expr` operators `and`/`or` (aliases `&&`/`||`) now use Python **logical**
  conjunction/disjunction with truthiness semantics (`a and b`, `a or b`), not
  bitwise `&`/`|`. For example, `6 and 3` now yields `3`, not `2`; `0 or 5`
  yields `5`. The result may be an operand value, not necessarily a boolean.
  (Roadmap R-01, option 1)

  Migration: templates that relied on integer bit arithmetic via `and`/`or` must
  use a different approach (e.g. nested arithmetic with `mul`/`add`/`mod`).

- Using a reserved name (`this`, `item`, `key`, `value`, `index`) as a variable
  name with `set`/`get` now raises `DefinitionError` instead of `AssertionError`.
  Previously the guard was implemented with `assert`, so under `python -O`
  (or `PYTHONOPTIMIZE`) it was removed entirely and such templates could silently
  overwrite the engine's own context slots, corrupting iteration state. The check
  is now always active. (Roadmap R-03)

  Migration: catch `transon.DefinitionError` instead of `AssertionError`; templates
  must not use reserved names as variables (they never worked correctly).

- Known leak sites for raw Python exceptions (`TypeError`, `KeyError`, etc.) now
  re-raise as `DefinitionError` or `TransformationError` with descriptive messages:
  `attr` invalid index types, `zip` non-iterables, `expr`/`call` bad `values`
  parameters or incompatible operands, `format` missing keys, iteration accessors
  and `parent` outside valid scope. Callers can rely on
  `except (DefinitionError, TransformationError)` as the complete error boundary.
  (Roadmap R-02, option 1)

  Migration: catch `transon.DefinitionError` / `transon.TransformationError`
  instead of raw `TypeError`, `KeyError`, or `IndexError` from transon rules.

- When a dynamic variable `name` evaluates to `NO_CONTENT`, `set` and `get` now
  raise `TransformationError` instead of silently using the sentinel as a variable
  key. `attr` returns `NO_CONTENT` uniformly when the dynamic name or any path
  segment is `NO_CONTENT` (previously list indexing raised `TransformationError`
  while dict lookup returned `NO_CONTENT` by accident). (Roadmap R-09, option 1)

  Migration: ensure computed variable names are defined before `set`/`get`; optional
  deep lookups via computed keys continue to work through `attr` returning no value.

- `join.sep` and `format.pattern` are now dynamic templates (walked like other rule
  parameters). A rule invocation or other template in these slots is evaluated at
  runtime instead of being used verbatim. `expr.op`, `call.name`, and `chain.funcs`
  list structure remain constant. (Roadmap R-16, option 2)

  Migration: templates that accidentally placed a marker dict in `join.sep` or
  `format.pattern` expecting it to be ignored will now be evaluated; use a literal
  string if you need a fixed separator or pattern.

- The default `template_loader` (used by `include` when none is configured) now raises
  `DefinitionError` instead of `RuntimeError`. Nested `include` calls are limited by
  `max_include_depth` on `Transformer` (default 50, overridable); exceeding the limit
  raises `TransformationError` with the include name chain (e.g. `A → B → A`).
  (Roadmap R-17, option 1 with name tracking)

  Migration: catch `DefinitionError` instead of `RuntimeError` for missing templates;
  configure `max_include_depth` if legitimate include chains exceed 50 levels, or
  refactor deeply nested includes.
