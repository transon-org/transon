# RFC: Editor-metadata export + projection-support rules

- **Status:** Proposed (2026-06-27). Engine-side counterpart of the `transon-blockly`
  *template-driven editor* pivot. The editor contract is recorded in
  `transon-blockly/docs/metadata-contract.md` §6 (§6.1–§6.3); this RFC is the engine repo's home for
  the work that contract depends on.
- **Type:** New engine capabilities (additive on top of v0.1.0; no behavior change to existing
  templates).
- **Roadmap:** tracked as R-23 (`switch`/`cond`), R-24 (`get_editor_metadata()`), R-25
  (`include` default-marker inheritance) in `docs/ROADMAP.md`.

## Why

The `transon-blockly` visual editor derives its **entire** surface — palette, toolbox, encoder,
decoder — as Transon-template *projections* of the engine's editor metadata, executed by the host
engine (the editor ships no engine and no hand-written mapping layer). For that to work the engine
must (1) expose a projection-ready metadata export, (2) provide lazy multi-way dispatch rules the
generated codec can run, and (3) let staged generator templates split across `include` boundaries
without losing their marker. None of these change the meaning of existing templates; they are purely
additive.

These are the only engine dependencies of the editor pivot. Keeping them tracked here (with the
editor contract as the consumer-side spec) is what keeps the two repos in sync.

## Deliverable 1 — `switch` / `cond` lazy-dispatch rules (R-23)

A lazy multi-way dispatch where **only the selected branch is evaluated** (unlike building a full
dict and indexing it, which would evaluate every arm).

- `switch` — equality dispatch on a key; cases as a JSON object, with an optional `default`.
- `cond` — Lisp-style ordered `[{when, then}, …]` with an optional `default` (subsumes `if`).

Used at runtime inside the generated codec (dispatch on rule name / block type) and inside the
projections to derive a widget from a parameter's `kind` + presence of `options`.

**Invariants (must hold, same as every built-in rule):**

- Honor `NO_CONTENT` discipline (skip/propagate per the engine's existing semantics).
- `DefinitionError` for a malformed template (e.g. `cond` arm missing `when`/`then`);
  `TransformationError` for incompatible data.
- Only the chosen branch is walked — non-selected `then`/case templates are never evaluated.
- Stdlib-only, Python 3.9+, never mutate input or template.
- Ordinary JSON rules — **no new transformation language** (`SPECIFICATION.md` purity invariant).

This is a `SPECIFICATION.md`-level addition (two new rules): propose the spec text, then implement
with table-driven example cases in `transon/tests/` (the cases that double as documentation).

## Deliverable 2 — `get_editor_metadata()` projection-ready export (R-24)

A dedicated, versioned editor-metadata export — **separate from the docs API** — emitting the shape
the editor's `metadata-contract.md` §2 requires. Greenfield: no editor-metadata export exists at
v0.1.0, so it is built directly in the projection-ready shape (no raw intermediate form).

The export must emit:

- **Pre-derived variant signatures** per rule (contract §2.5), computed in Python from the rule
  schema (`required`/`modes`) — one entry per valid mutually-exclusive parameter shape, each listing
  ordered visible params flagged `required`. The empty mode yields a valid zero-extra-param variant.
  Consumers must not re-derive these.
- Per-parameter **`kind`** (`dynamic` vs `constant`), declared at the rule source.
- **Resolved enum domains** (`options`) for closed constants (contract §2.6): `expr.op` → operator
  names + aliases; `call.name` → function names.
- Operator metadata (`name`, `alternative`, `kind`, `types`, `result`, `doc`, examples) and function
  metadata (`name`, `input`, `output`, `doc`, examples) — engine-native keys.
- A **split payload** (contract §2.7): a lean *structural catalog* (consumed by the generators) and a
  separate *examples/docs payload* (descriptions + tagged-corpus examples), joined by `name`.
- A standalone **`metadata_version`**.

**The line not to cross (contract §2.8):** the export states **engine facts only**. No Blockly
shapes — no colours, `message0`, field types, widget choices. The widget decision is derived in the
projection from `kind` + `options`; the engine stays Blockly-agnostic.

The function name/module are the engine repo's to finalize; the editor references it as
`get_editor_metadata()`. The editor side runs engine-parity checks
(`transon-blockly/docs/traceability.md`) that will fail if the export drifts from the contract.

## Deliverable 3 — `include` default-marker inheritance (R-25)

When an `include`d template does not pin its own marker, it inherits the **parent's default marker**
rather than always assuming `"$"`. This keeps the editor's staged generator templates (the `@`/`$`
compile phases) consistent across `include` boundaries.

Constraints:

- **No** free per-call `marker` argument on `include` (it invites silent misinterpretation).
- **No** `eval`/`apply` added to the engine — the editor's two-pass *generate-then-run* model needs
  none, and adding them widens the security surface.
- `quote`/`raw` is **declined** — the two-marker staging the editor uses covers literal-`$` emission.

This is small but **SPEC-first**: it changes `include` resolution, so update `SPECIFICATION.md` and
the `include` docstring, and add a focused test for the inheritance behavior.

## Non-goals

- No engine runtime is bundled into the editor; the editor only consumes this contract.
- No Blockly/editor knowledge enters the engine (contract §2.8).
- No change to existing template semantics: all three items are additive (new rules, a new export
  function, and a strictly-more-permissive `include` marker default that only affects `include`d
  templates which previously force-assumed `"$"`).

## Cross-repo provenance

- Consumer contract: `transon-blockly/docs/metadata-contract.md` §6 (§6.1 ↔ R-23, §6.2 ↔ R-24,
  §6.3 ↔ R-25), §2.5–§2.8, §3.
- Decisions ratified as `transon-blockly` open questions OQ-012 (`switch`+`cond`), OQ-013 (no
  `quote`/`raw`), OQ-014 (`include` marker inheritance), OQ-015 (split payload) on 2026-06-27.
- Architecture: `transon-blockly/docs/ARCHITECTURE.md` AD-026…AD-031.
