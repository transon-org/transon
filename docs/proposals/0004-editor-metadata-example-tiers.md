# RFC 0004 — Export example tags + curated example tiers in the editor metadata

- **Status:** Implemented (v0.1.5, 2026-07-02)
- **Created:** 2026-07-02
- **Roadmap:** R-29 (export tags + tiers), R-30 (grow curated corpus) — both `done`
- **Type:** Additive metadata-**export** change + **content-only** corpus growth — no new rules, no change to template semantics/validation or the docs API shape. `METADATA_VERSION` `2.1` → `2.2`
- **Consumers:** `transon-blockly` (`docs/metadata-contract.md` §2.7; SPEC-first there, its FR-009 / §12.8)
- **Supersedes / Superseded by:** — / —

> **Context.** Engine-side counterpart of the `transon-blockly` demo/examples enhancement: the
> editor's Examples surface currently flattens the reference corpus into one ~147-entry dropdown of
> test-fixture-named cases, because the export gives it no curation signal. Completes the *docs
> payload* the way [RFC 0003](0003-editor-metadata-structural-params.md) (R-28) completed the
> *structural catalog*: the engine already owns the facts (case tags, curated tiers) but the export
> drops them.

## Why

The tagged `TableDataBaseCase` corpus is the engine's single example source. As of v0.1.4 it holds
**115 distinct cases**, 87 of them multi-tagged (e.g. `['chain', 'join', 'map:item', 'item']`), and
reference coverage is complete — no rule, parameter, operator, or function entry in
`get_editor_metadata()` has an empty `examples` list. The corpus also already contains two
**curated tiers** with real-world framing and a docstring quality gate (`tests/test_docs.py`):

- `worked-example` — 6 cases (`transon/tests/test_worked_examples.py`): reshape records,
  filter-and-project, index-by-key, rename-and-flatten, optional-fields/defaults, nested arithmetic.
- `recipe` — 7 cases (`transon/tests/test_recipes.py`): task-oriented "how do I…" patterns.

`get_all_docs()` (the docs-site API) exposes both tiers as first-class blocks. But
`get_editor_metadata()` exposes **neither**, and its example serializer
(`docs.get_test_cases_for_tag()`) emits only `{name, doc, template, data, result}` — **stripping
`tags`**, the corpus's own organizing metadata. Downstream consequences in the editor:

- The Examples picker can only flatten the per-entry reference examples into one long list of
  fixture-named cases (`SetInvisibleToEarlierSiblingKey`, …) — a reference corpus posing as a demo
  showcase.
- Because a multi-tagged case is re-inlined under every entry it documents, the docs payload
  carries **245 inlined example objects for 115 distinct cases** (~100 KB docs vs ~7 KB catalog),
  and the editor must dedupe by content hash instead of by name.

## Deliverable 1 — export tags + curated tiers (R-29)

`get_editor_metadata()` gains, additively:

1. **`tags` on every serialized example.** Add `'tags': list(case.tags)` in the shared serializer
   (`docs.get_test_cases_for_tag()`). This also flows into `get_all_docs()` — additive there too;
   the docs site ignores unknown fields. Tags are **engine facts** (what a case demonstrates),
   consistent with contract §2.8. With `name` + `tags` present, the editor dedupes by name and can
   group/filter/context-link examples (e.g. show `set` scoping cases when a `set` block is
   selected) without re-deriving anything.
2. **`docs.worked_examples` and `docs.recipes`** blocks, mirroring `get_all_docs()` (same
   serializer, tags included). This hands the editor its curated demo tier directly.
3. **`METADATA_VERSION` `2.1` → `2.2`**; tests extend `tests/test_metadata.py` (tags present on
   entry-, param-, operator-, and function-level examples; both tier blocks non-empty; version
   bump).

**Conventions to keep (state them in the docstrings):**

- Curated cases carry **only** their tier tag (`['recipe']` / `['worked-example']`) so they never
  pollute the per-rule/param reference galleries; reference cases never carry a tier tag.
- The engine does **not** emit display order, difficulty, titles, or any presentation vocabulary —
  the editor owns those in its projection-data file (its FR-127), per contract §2.8.

## Deliverable 2 — grow the curated corpus (R-30, content only)

The curated tiers predate `switch`/`cond` (R-23) and skip several rules users reach for early.
Add roughly five recipes and one worked example, at the existing docstring quality bar
(task-framed bold title + *"Task: …"* line; `tests/test_docs.py` name lists extended):

- **Recipe — map a code to a label** (`switch` with `default`): the canonical status-code →
  display-string dispatch.
- **Recipe — bucket a value by ranges** (`cond` arms with comparisons): "small/medium/large".
- **Recipe — compute once, use twice** (`set`/`get`): store a derived value, reference it in two
  output fields.
- **Recipe — pair up two lists** (`zip`): merge parallel lists into records.
- **Recipe — keep items matching a condition** (`filter` + `expr`): filter on a comparison, not
  just truthiness (complements the existing worked example).
- **Worked example — conditional enrichment inside a map** (`map` + `switch`/`cond` + `object`):
  a per-record transformation with branch logic, the shape most "real" templates take.

Exact list is the implementer's to adjust; the requirement is that every rule family a first-time
user meets (`accessors`, `map`/`filter`, `object`, `expr`, `switch`/`cond`, `set`/`get`, `zip`,
`format`/`join`/`call`) appears in at least one curated case.

## Options considered and deferred

- **Normalize the docs payload to one flat tagged corpus** (entries reference examples by name):
  halves the payload and removes inlining duplication, but it is a **shape break** (contract §2.7
  specifies inline examples) — a `3.0` candidate, not now. Deliverable 1's `name` + `tags` already
  enable editor-side name-dedup, capturing most of the benefit.
- **New `use-case:` / `level:` tag namespaces:** deferred. The tier tags plus topical tags cover
  the editor's grouping needs; difficulty/ordering is editor-owned presentation. Orthogonal
  namespaces stay cheap to add later (tag harvesting is exact-match, so they are inert).
- **Exporting the `errors` block** (`get_error_examples()`): deferred until the editor's
  error-taxonomy surface asks for it; additive whenever needed.

## Non-goals

- No Blockly/editor knowledge enters the engine (contract §2.8): no titles, categories, ordering,
  difficulty, or widget vocabulary.
- No change to rules, validation, the walker, or template semantics; no docs-site changes required.
- No renaming or re-tagging of existing reference cases.

## Cross-repo provenance

- Consumer contract: `transon-blockly/docs/metadata-contract.md` §2.7 (examples/docs payload) —
  update to `2.2` follows this RFC; its §2.1 note that the editor "sources examples from the tagged
  corpus" becomes literally true (tags travel).
- Editor consumption (that repo, SPEC-first): curated tier in the Examples picker (its FR-009 /
  §12.8), `ExampleCase.tags` switching from invented family tags to engine tags, name-based dedupe,
  snapshot regeneration (`update_memory.py --snapshot`) and engine-parity check updates.
- Evidence audit: this RFC's counts (115 cases / 87 multi-tagged / 245 inlined / zero empty
  entries) measured against v0.1.4 (`METADATA_VERSION` 2.1) on 2026-07-02.
