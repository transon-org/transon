# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.6] - 2026-07-02

### Changed

- **Breaking (export shape only):** examples in the docs/metadata APIs are
  normalized. `get_all_docs()` and `get_editor_metadata()` now embed one flat
  `examples` corpus (every case serialized exactly once, with `tags`), and every
  other `examples` field — rule-, parameter-, operator-, and function-level,
  plus the `worked_examples`/`recipes` tiers — is an ordered list of `name`
  references into it. The `errors` block stays inline. Previously 121 corpus
  cases were re-inlined as 264 example objects (~60 % of each payload).
  `METADATA_VERSION` bumps `2.2` → `3.0`; no change to rules, validation, or
  template semantics. The two previously untagged corpus cases
  (`AttrSimplePathDoesNotExist1/2`) are now tagged `attr:names` and appear in
  the exports. (Roadmap R-31)

## [0.1.5] - 2026-07-02

### Added

- Every example serialized by the docs/metadata APIs now carries its corpus
  `tags` (engine facts: what a case demonstrates), so consumers can dedupe
  multi-tagged cases by `name` and group examples without re-deriving anything.
  `get_editor_metadata()` additionally exposes the two curated example tiers —
  `docs.worked_examples` and `docs.recipes` — mirroring `get_all_docs()`.
  Additive only — `METADATA_VERSION` bumps `2.1` → `2.2`; no change to rules,
  validation, or template semantics. (Roadmap R-29)
- Curated example corpus grown to cover every rule family a first-time user
  meets: five new recipes (`switch` code→label dispatch, `cond` range
  bucketing, `set`/`get` compute-once-use-twice, `zip` list pairing, `filter` +
  `expr` comparison) and one new worked example (conditional enrichment inside
  a `map` with `switch`/`cond` branch logic). Content only. (Roadmap R-30)

## [0.1.4] - 2026-07-02

### Added

- `get_editor_metadata()` now exports the structural param facts the engine already
  declares and validates: `container` (`mapping`/`list`/`arms`; omitted for the
  default `template`) on `chain.funcs`, `object.fields`, `switch.cases`, and
  `cond.cases`, plus the `arm: {required, params}` slot schema for `ARMS` params
  (serialized recursively with the same shape as rule params). The docs payload's
  `cond.cases` entry gains an `arms` list carrying the `when`/`then` slot
  docstrings. Additive only — `METADATA_VERSION` bumps `2.0` → `2.1`; no change to
  rules, validation, or template semantics. (Roadmap R-28)

## [0.1.3] - 2026-06-29

### Added

- `type` `call` function: a **total**, non-throwing function returning a value's
  JSON type name (`object`/`array`/`string`/`int`/`float`/`boolean`/`null`). It is
  the one operation a `switch`/`cond` key can safely apply to a node of unknown
  type, letting the visual editor's generated codec dispatch on JSON type with a
  single `switch`. Flows through `get_editor_metadata()` (so `call.name` gains
  `type`) and the docs. (Roadmap R-26)
- `include` now propagates the active `template_loader` to recursive /
  self-`include`ing sub-templates. The `template_loader` is always called as
  `loader(name, context=...)` and handed an `IncludeContext` (parent loader, marker,
  depth guard, include-stack) from which it **constructs** the sub-`Transformer`
  itself (e.g. `context.transformer(template)`) instead of the engine mutating the
  loaded instance — so a loader may safely return a cached/shared `Transformer`.
  `context` is optional in the loader signature (so a loader may also be invoked
  standalone). **Breaking:** a `template_loader` must accept the `context` keyword.
  Adds the public `IncludeContext` and an `include_stack` constructor parameter.
  (Roadmap R-27)

## [0.1.2] - 2026-06-29

### Fixed

- `get_editor_metadata()` no longer raises `PackageNotFoundError` when `transon`
  is importable from source but not installed as a distribution; `engine_version`
  degrades to `None` in that case. This lets downstream consumers (e.g. the
  visual editor's engine-parity check against a sibling checkout) load the export.
  (Roadmap R-24)

## [0.1.1] - 2026-06-27

### Added

- `switch` and `cond` lazy multi-way dispatch rules: `switch` does equality
  dispatch on a `key` against a `cases` mapping; `cond` walks ordered
  `[{when, then}]` arms (subsuming `if`/`else`). Only the selected branch is
  evaluated, and both honor `NO_CONTENT` and `default`. (Roadmap R-23)
- `transon.metadata.get_editor_metadata()`: a projection-ready, versioned
  editor-metadata export (separate from the docs API) for the `transon-blockly`
  visual editor. Emits a split structural `catalog` / `docs` payload with
  pre-derived variant signatures (`derive_variants`), per-parameter `kind`
  (`dynamic`/`constant`), and resolved enum `options` for closed constants
  (`expr.op`, `call.name`). Engine facts only — no Blockly shapes. (Roadmap R-24)

### Changed

- `register_rule` now declares each rule's parameter schema with a single
  `_variants` keyword — the closed set of valid complete parameter shapes — which
  unifies and replaces the former `_required` and `_modes` arguments. Parameters
  shared by every variant are the always-required ones; parameters that distinguish
  variants are the mutually exclusive groups. The required/mode set algebra is
  derived from `_variants` internally, so validation diagnostics and editor metadata
  are unchanged.
- `register_rule` also gains `_constants`, `_containers`, and `_arms` keyword
  arguments so each parameter declares its `kind` and structural shape at the rule
  source, using the exported `enum.Enum` types `ParamKind`, `ContainerType`, and
  `Domain`. `_arms` (built with the new `arm()` helper, which likewise takes
  `_variants`) declares an ordered list of objects whose slots are declared and
  validated the **same way as parameters**. Static validation is now **fully
  generic** — driven entirely by these per-parameter descriptors with no
  special-casing by rule or parameter name (the former hardcoded `object.fields` /
  `expr.op` / `call.name` / `chain.funcs` and the `cond`-shaped arm branch are gone).
  Behavior is unchanged for every previously valid template. (Roadmap R-24)
- `include` now lets a loaded sub-template that still uses the default marker (`$`)
  **inherit the parent transformer's marker**, keeping staged templates consistent
  across `include` boundaries. A sub-template that pins a non-default marker keeps
  it; there is no per-call `marker` argument. (Roadmap R-25)

## [0.1.0] - 2026-06-15

First `0.1.x` milestone: the engine-semantics roadmap (`R-01…R-22`) and the
docs-site content roadmap (`D-01…D-19`) are both complete. No breaking changes
since `0.0.13`; this release marks the v0 feature set as stable.

### Added

- Docs pipeline: `transon.docs.get_all_docs()` now emits top-level
  `worked_examples`, `recipes`, and `errors` arrays, harvested from new corpus
  galleries (`transon/tests/test_worked_examples.py`, `test_recipes.py`,
  `test_error_model.py`) via the `worked-example` / `recipe` / `error` tags, with
  drift-guards in `tests/test_docs.py`. A new `ErrorBaseCase` corpus type asserts
  the exact `str(exception)` so published error text can't drift. (Docs-site D-15,
  D-16, D-17)
- Docs: a "How evaluation works" section in the `Transformer` class docstring —
  the on-page mental model (recursive tree walk, marker-based rule detection,
  context/scope for iteration accessors, `NO_CONTENT` skip propagation), linking to
  the specification for exhaustive detail. (Docs-site D-18)

### Changed

- Operator and function documentation is now stored at registration time on
  `register_operator` / `register_function` (and exposed via `get_operators()` /
  `get_functions()`) instead of detached tables, keeping the registry the single
  source of truth for the generated docs. (Docs-site D-08 follow-up)

## [0.0.13] - 2026-06-14

### Changed

- README: add a "Comparison" section with a "best when" decision table, honest
  trade-offs, and a JSONata-vs-transon side-by-side example. (Docs-site D-19)
- Docs: add a "What is transon?" framing block to the `Transformer` class
  docstring (problem statement, inspirations, design principles, analogues) and fix
  the getting-started snippet. (Docs-site D-07, D-10)

## [0.0.12] - 2026-06-14

### Changed

- `Context.derive()` no longer eagerly copies all parent variables into every child
  scope. Derived contexts store only new props; `get` walks the parent chain for reads;
  the first `set` in a derived scope materializes inherited variables (copy-on-write).
  R-15 scoping semantics are unchanged for sequential template evaluation.
  (Roadmap R-22, option 1 with copy-on-write)

### Added

- Documented `set`/`get` variable scoping for template authors: rule docstrings,
  spec §2.2 scoping table, and seven example cases in `transon/tests/test_set.py`
  (sibling dict keys, first vs later `chain` func, `map` isolation). Behavior
  unchanged. (Roadmap R-15, option 1)

- `transform(data, no_content=None, *, copy_output=False)` gained an opt-in
  `copy_output` keyword. When `True`, the result is `copy.deepcopy`-ed once at the
  `transform()` boundary, so it shares no mutable structure with the input. By default
  (`False`) pass-through rules (`this`/`attr`/`get`/`item`/…) still return references
  into the input — mutating the output then mutates the original input. This aliasing
  is now documented prominently (spec §3.1, §10) so callers who post-process the result
  know to opt in. Default behavior is unchanged. (Roadmap R-13, option 2)

## [0.0.11] - 2026-06-13

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
