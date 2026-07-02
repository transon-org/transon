# RFC: Normalize exports to one flat example corpus (name references, no inlining)

- **Status:** Implemented (2026-07-02) — engine side shipped as R-31 (`METADATA_VERSION` `3.0`);
  consumer migrations (Deliverable 2) tracked in the consumer repos. Originally proposed
  2026-07-02. Picks up the option explicitly deferred in the R-29 RFC
  (`editor-metadata-example-tiers.md`, "Options considered and deferred"): *normalize the docs
  payload to one flat tagged corpus; entries reference examples by name*. R-29 shipped the enabling
  half (`name` + `tags` on every serialized example); this RFC removes the inlining itself.
- **Type:** **Shape-breaking** change to both export APIs — `get_all_docs()` (docs-site API) and
  `get_editor_metadata()` (editor export). No new rules, no change to template semantics,
  validation, or the corpus content. `METADATA_VERSION` `2.2` → `3.0`.
- **Roadmap:** R-31 in `docs/ROADMAP.md` (done), following R-29/R-30 (example tags + curated
  tiers).
- **Consumers:** `transon-org.github.io` (docs site + playground) and `transon-blockly`
  (contract `metadata-contract.md` §2.7 — SPEC-first update in that repo). Both are ours; the
  migrations are coordinated, small, and listed below.

## Why

Both exports share one serializer (`docs.get_test_cases_for_tag()`) and both **re-inline the full
example object** (`{name, doc, template, data, result, tags}`) under every entry a case's tags
attach it to: rule-level (`"<rule>"`), parameter-level (`"<rule>:<param>"`), operator-level
(`"op:<alternative>"`), function-level (`"func:<name>"`), and the two curated tiers.

Measured against the current tree (engine v0.1.5, `METADATA_VERSION` 2.2, 2026-07-02):

- The corpus holds **121 distinct cases**; the exports inline **264 example objects**
  (119 distinct names). The worst offenders (`MapListsToDict`, `SwitchDispatchOnKey`,
  `CondFirstTruthyArm`, `AttrDynamicReferenceMultipleNames`) are inlined **5× each**.
- `get_all_docs()` weighs ~139 KB; `get_editor_metadata()` ~131 KB — a **6 KB** structural
  `catalog` next to a **124 KB** docs payload. Serializing every case exactly once is ~49 KB, so
  **~75 KB (~60 %) of each payload is repeated example bodies**.
- Consumers already pay for the duplication in code: the editor's `buildExampleCorpus()`
  deduplicates by **content hash** (pre-2.2 the `name` field wasn't reliable enough); the docs site
  renders whatever arrives, shipping every duplicate to the browser.
- Two corpus cases (`AttrSimplePathDoesNotExist1/2`, `tags = []`) appear in **no** export at all —
  silently invisible, and in violation of `SPECIFICATION.md` §6.1 ("`tags` is mandatory"). Inlining
  hides such orphans; a flat corpus makes every case's presence (or absence) checkable.

The duplication is structural, so it grows with the corpus: every new multi-tagged case (R-30
encourages exactly those) multiplies itself across every entry it documents.

## Deliverable 1 — flat corpus + name references (both exports)

### 1.1 New shared corpus block

`transon/docs.py` gains `get_example_corpus()`: **every** valid `TableDataBaseCase` serialized
exactly once, in stable corpus order, in the existing shared shape:

```json
"examples": [
  {"name": "...", "doc": "...", "template": {...}, "data": ..., "result": ..., "tags": [...]},
  ...
]
```

A list (not a name-keyed object) for consistency with the rest of the contract, which joins
list entries by `name` (metadata contract §2.7); `name` stays the unique join key (uniqueness
becomes a tested invariant, see 1.4).

### 1.2 Entries reference by name

Every place that today inlines example objects instead carries an ordered list of names, with the
same membership and order the tag join produces today:

- `get_all_docs()`: rule / param / operator / function `examples` become `["CaseName", ...]`;
  top-level `worked_examples` and `recipes` become name lists; a top-level `examples` block (1.1)
  is added. The `errors` block is untouched (error cases already appear exactly once and live in a
  different shape).
- `get_editor_metadata()`: same treatment inside `docs` — `docs.examples` (flat corpus) plus name
  lists on `docs.rules[*]` / `params[*]` / `operators[*]` / `functions[*]` /
  `docs.worked_examples` / `docs.recipes`.

**The join stays engine-owned.** Consumers resolve names against the flat corpus; they do **not**
re-derive membership from tags. The tag conventions (`op:<alternative>`, `func:<name>`,
`<rule>:<param>`, tier tags) remain an engine implementation detail, consistent with the
"consumers read pre-derived facts, never re-derive" principle established for variants (§2.5).
`tags` still travel on each corpus entry — they remain useful engine facts for grouping/filtering
(R-29 rationale) — but they are not the join mechanism.

### 1.3 Versioning

- `METADATA_VERSION` `2.2` → **`3.0`** (shape break, anticipated by the R-29 RFC).
- `get_all_docs()` has no schema version of its own (only the package `version`); the docs-site
  update ships in lockstep (the site bundles the engine via Pyodide, so site deploy and engine
  version move together — see Deliverable 2).

### 1.4 Tests and invariants

Extend `tests/test_metadata.py` / docs tests:

- every name referenced anywhere resolves to exactly one corpus entry (no dangling refs, no
  duplicate names);
- **every corpus case is reachable** from at least one reference list — this is the new gate that
  catches untagged orphans like `AttrSimplePathDoesNotExist1/2` (fix those two by tagging or
  explicitly excluding them as part of this work);
- membership and order of each name list equals what the 2.2 tag join produced (no silent content
  change riding along with the shape change);
- curated-tier convention unchanged: tier cases carry only their tier tag and never appear in
  reference galleries; reference cases never carry a tier tag.

## Deliverable 2 — consumer migrations (coordinated)

### 2.1 Docs site (`transon-org.github.io`)

`public/script.py` passes `get_all_docs()` through verbatim — no change. TypeScript side:

- `src/types.ts`: entry `examples` fields become `string[]`; `IDocsData` gains
  `examples: IExampleData[]`.
- Components (`Rule`, `Param`, `Operator`, `Function`, `WorkedExamples`, `Recipes`,
  `ExamplesSection`) resolve names via one `Map<string, IExampleData>` built once in `App`.

Net effect: identical rendering, ~60 % smaller payload crossing the Pyodide→JS boundary.

### 2.2 Editor (`transon-blockly`, SPEC-first in that repo)

- `docs/metadata-contract.md` §2.7 currently specifies **inline** examples — update the contract
  to the flat-corpus + name-reference shape (that repo's governance: SPEC/contract first).
- `buildExampleCorpus()` collapses: read `docs.examples` directly — the content-hash dedupe and
  name-collision suffixing become dead code (every case appears once, names are unique by 1.4).
- Regenerate the committed pin (`update_memory.py --snapshot`); engine-parity checks
  (`check_engine_parity.py`) follow the new shape.

## Deliverable 3 — align `SPECIFICATION.md` after implementation

The engine spec must be updated **after** (with) the implementation, and this is also the moment
to sweep other discrepancies — the shape sketches are already stale against 2.2:

- **§5 (docs generator):** the `get_all_docs()` JSON sketch shows only `version`/`doc`/`rules` —
  it omits the `worked_examples`, `recipes`, `errors`, `operators`, and `functions` blocks and the
  `tags` field added by R-29. Rewrite it to the new flat-corpus shape (and make it complete this
  time).
- **§5.1 (editor-metadata export):** the sketch omits `docs.worked_examples` / `docs.recipes`,
  example `tags`, and the `container` / `arm` catalog-param keys (R-28). Rewrite to the `3.0`
  shape.
- **§6.1:** "`tags` is mandatory" is currently violated by the two empty-tag cases — resolve
  (tag them or amend the rule with an explicit exclusion) so spec and corpus agree.
- While editing, audit §5/§5.1 prose for any further drift (e.g. serializer field lists) — the
  known items are the three above, but the sweep is part of the deliverable, since **any other
  discrepancies found during implementation must be fixed in the same pass**.

## Options considered and rejected

- **Tags-only (drop the reference lists; consumers filter the flat corpus by tag):** smallest
  payload, but it moves the tag conventions (`op:<alternative>`, `func:<name>`,
  `"<rule>:<param>"`) into every consumer — exactly the re-derivation the contract forbids for
  variants and enum domains. Rejected.
- **Status quo + consumer-side name dedupe (the R-29 position):** already shipped; it fixes
  correctness of dedupe but not the payload or the growth curve, and leaves untagged orphans
  invisible. Insufficient as an end state.
- **Name-keyed object instead of a list for the corpus:** O(1) join without building an index,
  but inconsistent with the rest of the contract (lists joined by `name`) and loses explicit
  ordering. Rejected; consumers build one index.
- **Flatten `errors` too:** no duplication exists there (each error case appears once, nothing
  references them), so normalizing adds churn without benefit. Deferred until something needs to
  reference error cases by name.

## Non-goals

- No change to rules, validation, the walker, or template semantics; no corpus re-tagging beyond
  fixing the two empty-tag cases.
- No presentation vocabulary in the export (order, difficulty, titles remain consumer-owned —
  contract §2.8).
- No compatibility shim emitting both shapes: both consumers are ours and migrate in lockstep;
  `metadata_version` `3.0` is the fence for anyone else.

## Cross-repo provenance

- Prior art: `docs/proposals/editor-metadata-example-tiers.md` (R-29) — this RFC is its deferred
  "normalize to one flat tagged corpus" option, promoted.
- Consumer contract: `transon-blockly/docs/metadata-contract.md` §2.7 (currently specifies inline
  examples) — contract update follows this RFC, SPEC-first in that repo.
- Docs site: `transon-org.github.io` — `src/types.ts` + rendering components.
- Evidence audit: all counts (121 cases / 264 inlined / 119 distinct / ~139 KB / ~131 KB /
  ~49 KB flat / 2 untagged orphans) measured against engine v0.1.5, `METADATA_VERSION` 2.2, on
  2026-07-02.
