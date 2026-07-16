# RFC 0003 — Export structural param facts (`container` + `arm`) in the editor metadata

- **Status:** Implemented (v0.1.4, 2026-07-02)
- **Created:** 2026-07-02
- **Roadmap:** R-28 (`done`)
- **Type:** Additive metadata-**export** change — no new rules, no change to template semantics or validation. `METADATA_VERSION` `2.0` → `2.1`
- **Consumers:** `transon-blockly` (`docs/metadata-contract.md` §2.2)
- **Supersedes / Superseded by:** — / —

> **Context.** Engine-side counterpart of the `transon-blockly` UAT follow-up "collection/struct
> inputs" (editor UAT findings #1/#2: structured rule parameters — `cond.cases`, `chain.funcs`,
> `object.fields`, `switch.cases` — currently degrade into compositions of generic array/object
> blocks instead of one coherent block per rule). The cross-repo decision (engine-first; no
> editor-side shape catalog) is recorded in `transon-blockly/docs/current-state.md` (Last action,
> 2026-07-02); the consumer contract update (`transon-blockly/docs/metadata-contract.md` §2.2)
> follows this RFC. Completes the R-24 export from [RFC 0001](0001-editor-metadata-export.md): R-24
> shipped `kind`/`options`/`variants`; this RFC stops **dropping** the two structural facts the
> engine already declares and validates internally but never emits — a param's *container shape* and,
> for arm-lists, the *arm schema*.

## Why

The editor derives its entire surface (palette, toolbox, encoder, decoder) as projections of
`get_editor_metadata()`. Today the export describes every dynamic parameter identically — "a
template" — so the editor must render `cond.cases` (an ordered list of `{when, then}` arms) the
same way it renders `attr.name` (a single value): one generic socket, forcing users to hand-build
`array → object(when/then)` compositions on the canvas.

The engine, however, **already knows the difference** — declaratively, at the rule source, and
enforced by static validation (`Transformer.validate()`) and the walk:

- `ParamSpec.container` (`transon/transformers.py`, `ContainerType`):
  `TEMPLATE` (default) · `MAPPING` (literal keys → template values) · `LIST` (constant-structure
  array of templates) · `ARMS` (array of objects whose slots are declared like parameters).
- `ParamSpec.arm` (`ArmSpec`): for `ARMS` params, the arm's `required` slot names plus per-slot
  `ParamSpec`s (`kind`/`container`/`domain`) — declared via `arm(...)` with the same vocabulary
  as rule parameters, and enforced at runtime by `iter_arms`/`_check_arms`.

Current declarations (engine truth, v0.1.3):

| Rule param | `container` | Arm schema |
|---|---|---|
| `chain.funcs` | `list` | — |
| `object.fields` | `mapping` | — |
| `switch.cases` | `mapping` | — |
| `cond.cases` | `arms` | required `when`, `then`; both slots dynamic templates |
| every other param | `template` (default) | — |

`transon/metadata.py::_catalog_params` exports only `name`/`kind`/`options` and silently drops
`container`/`arm`. Without them the editor would need its own parallel shape catalog — exactly
the hand-maintained duplication the R-24 pivot removed (`metadata-contract.md` §2.8's rationale
cuts both ways: the engine must not know Blockly, and the editor must not re-declare engine
facts).

**These are engine facts, not presentation.** "The `fields` mapping has literal keys", "the
`funcs` list structure is constant", "a `cases` arm requires `when` and `then`" are validation
semantics the engine enforces today. What the editor *renders* for them (repeating inputs,
labeled groups, key/value rows) stays a projection decision on the editor side — the §2.8 line
("no Blockly shapes, colours, or widget choices") is untouched.

## Deliverable — emit `container` and `arm` from `_catalog_params` (R-28)

In the **structural catalog** (`catalog.rules[*].params[*]`):

- Emit `container: "mapping" | "list" | "arms"` when the param's `ContainerType` is not the
  default; **omit the key entirely for `TEMPLATE`** (additive: unannotated params look exactly as
  they do in 2.0).
- For an `ARMS` param, also emit the serialized arm schema:

```json
{
  "name": "cond",
  "params": [
    {
      "name": "cases",
      "kind": "dynamic",
      "container": "arms",
      "arm": {
        "required": ["when", "then"],
        "params": [
          { "name": "when", "kind": "dynamic" },
          { "name": "then", "kind": "dynamic" }
        ]
      }
    },
    { "name": "default", "kind": "dynamic" }
  ],
  "variants": [ { "id": "base", "params": [ "…unchanged…" ] } ]
}
```

- `arm.params` entries use the **same serialization as rule params** (`name`, `kind`, plus
  `container`/`options`/`arm` under the same omit-when-default rules). Today's only arm
  (`cond.cases`) has two plain dynamic slots, so nesting never recurses in practice — but the
  serializer should be written recursively so a future arm with a constant slot (dropdown in an
  arm) or a container slot folds in with no export change.
- `chain.funcs` gains `"container": "list"`; `object.fields` and `switch.cases` gain
  `"container": "mapping"`. Nothing else in the catalog changes.
- **Faithfulness note:** `arm(...)` collapses its `_variants` at declaration time — `ArmSpec`
  stores only `required` + `params`. The export therefore emits exactly that (no invented
  `variants` key). If a future arm ever needs true mutually-exclusive slot modes, extending
  `ArmSpec` is a separate, additive decision.

In the **docs payload** (`docs.rules[*].params[*]`, optional but recommended): the `cases` param
entry gains an `arms` list carrying each slot's declared docstring (`when=`/`then=` in the
`arm(...)` call), so the editor can tooltip the projected sub-inputs:

```json
{ "name": "cases", "description": "…", "arms": [
  { "name": "when", "description": "Predicate template for this arm. …" },
  { "name": "then", "description": "Result template, evaluated only when this arm is selected. …" }
] }
```

**Versioning:** bump `METADATA_VERSION` to `2.1` (additive keys only; consumer contract §5
treats this as a compatible minor bump — the editor's NFR-040 check flags, not fails).

**Tests** (extend `tests/test_metadata.py`, same style as `test_expr_op_options_resolved`):

- `chain.funcs` exports `container == "list"`; `object.fields`/`switch.cases` export
  `container == "mapping"`.
- `cond.cases` exports `container == "arms"` with `arm.required == ["when", "then"]` and both
  slots `kind == "dynamic"`.
- Every other param of every rule has **no** `container`/`arm` key.
- Docs payload: `cond.cases` carries the two arm-slot descriptions.
- `metadata_version == "2.1"`.

## Invariants (unchanged from R-24)

- **Engine facts only** — no Blockly vocabulary enters the export (§2.8). `container`/`arm`
  describe what `validate()`/the walk already enforce, nothing more.
- Additive: a 2.0 consumer reading a 2.1 payload sees only extra keys; no existing key changes
  shape or meaning.
- Stdlib-only, Python 3.9+; no change to `transon/rules.py`, the walker, validation, or any
  template's behavior.

## Non-goals

- **No widget/presentation hints** (repeating-group, dropdown, colour — editor-owned, §2.8/§2.9).
- **No re-annotation of TEMPLATE params.** `map.items`, `join.items`, `expr.values`, `zip.items`
  stay unannotated *deliberately*: they accept fully dynamic templates (e.g.
  `{"$": "attr", …}`), so a single value socket is the semantically honest editor rendering.
  Marking them `list` would be false.
- No new `ContainerType`, no new rules, no `ArmSpec.variants` extension (see faithfulness note).
- No change to `derive_variants` / variant signatures.

## Consumer side (editor repo, follows this RFC — not in scope here)

Recorded in `transon-blockly/docs/current-state.md` (Next steps): metadata snapshot re-pin +
engine-parity check extension; `metadata-contract.md` §2.2 gains `container`/`arm`; new FRs; then
the projection work (`G_palette` container branch, ~2 new rule-agnostic Blockly runtime
primitives, `G_encode`/`G_decode` container arms, round-trip corpus extension) — spiked on
`chain` (list) + `cond` (arms) before generalizing, gated by that repo's `round-trip-reviewer`.

## Cross-repo provenance

- Decision (engine-first shape hints; editor-side `paramShapes` stopgap **rejected** as a
  parallel semantic catalog): `transon-blockly` UAT brainstorm, 2026-07-02, recorded in its
  `docs/current-state.md` handoff.
- Consumer contract: `transon-blockly/docs/metadata-contract.md` §2.2 (parameter metadata — to be
  updated), §2.8 (the line not to cross — unchanged), §5 (schema versioning).
- Prior art: [RFC 0001](0001-editor-metadata-export.md) (R-23..R-25),
  [RFC 0002](0002-type-function.md) (R-26..R-27).
