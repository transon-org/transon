# RFC 0008 — Author-facing Language Reference: document, packaging, and export API

- **Status:** Accepted (2026-07-18) — awaiting implementation
- **Created:** 2026-07-16
- **Amended:** 2026-07-18 — consolidation scope extended to the `Transformer` docstring and
  `README.md`; single ownership principle (structure in the catalog, per-entity behavior in
  registration docs, cross-cutting semantics in `LANGUAGE.md`); no per-entity sections in
  `LANGUAGE.md`; sequencing decision (see below)
- **Roadmap:** R-34 (Language Reference document), R-35 (package the reference), R-36 (`get_language_reference()` export) — `accepted`, rows in `docs/ROADMAP.md`; docs-site counterpart is D-20 in `docs/DOCS_SITE_ROADMAP.md`. (R-33 is held by [RFC 0007](0007-builtin-function-library.md).)
- **Type:** New documentation artifact + packaging + a new read-only export API (`get_language_reference()`) — additive; no change to existing template semantics or engine API shapes. The **content** of `get_all_docs()['doc']` shrinks to the embedder-facing narrative as part of the consolidation (shape unchanged; the docs export carries no schema version, so the change is coordinated by release note in `CHANGELOG.md`). Symmetrically, per-rule doc **content grows** in both exports (`get_all_docs()` and `get_editor_metadata()['docs']`) as §4's facts fold into the docstrings — also shape-unchanged, doc text is contractually opaque
- **Consumers:** `transon-authoring` (authority ladder rung 2; `SKILL.md`, AD-018/NFR-001/NFR-003), `transon-org.github.io` (docs site)
- **Supersedes / Superseded by:** — / —

> **Context.** Engine-side counterpart of the `transon-authoring` authority-ladder gap: the skill
> contract (`transon-authoring/SKILL.md`, AD-018/NFR-001) names the engine specification as authority
> rung 2 for Transon semantics, but no author-facing, pinnable, offline-servable form of that document
> exists. This RFC is the engine repo's home for the work that closes the gap.

## Why

`docs/SPECIFICATION.md` is the **engine** specification: roughly half of it is contributor
material — repository layout (§1), the `Transformer` Python API and extension registries (§3),
the documentation pipeline (§5), testing conventions (§6), the add-a-rule checklist (§7),
versioning (§8), invariants (§9–10), known issues (§12). The **language** — what a template
author needs — lives only in §2 (marker, context, `NO_CONTENT`, error model), §4 (built-in rule
reference), and §11 (data flow), interleaved with the rest. That language half reaches consumers
through **two channels**: the cross-cutting narrative (§2/§11) becomes `LANGUAGE.md`, while the
per-entity facts (§4) travel through the registration docs and the exports that already carry
them (see the ownership principle, Deliverable 1).

Two consumers need the cross-cutting narrative, by itself, offline, pinned to an engine version:

1. **`transon-authoring`** — its agents ground drafts in the metadata snapshot (which carries
   the structural catalog **and** the per-entity descriptions and examples,
   `get_editor_metadata()['docs']`) and the verify gate (pass/fail shows *behavior*), but have
   nothing that explains the **cross-cutting** semantics no per-entity description can state:
   `NO_CONTENT` propagation across containers, `DefinitionError` vs `TransformationError`,
   scoping, empty-list `expr` reduction. Repair loops burn their bounded budget rediscovering
   facts a reference section would state. The skill's harnesses mount no repo checkout, so the
   document must travel inside the installed package, like the metadata snapshot does.
2. **Human authors / the docs site** — the only narrative the site renders today is the
   audience-mixed `Transformer` class docstring (see below); no author-scoped, spec-grade
   narrative source exists.

Shipping `SPECIFICATION.md` itself is the wrong fix: it tells an authoring agent about extension
registries and subclassing (capabilities outside the authoring profile) and about open design
questions — content an author must not act on.

The specification is also not the only pre-existing copy of the semantics. The `Transformer`
class docstring (~225 lines, exported today as `get_all_docs()['doc']` and rendered by the docs
site) restates marker detection, context/scoping, and `NO_CONTENT` propagation a **third** time —
interleaved with install instructions, the project pitch (itself duplicated against `README.md`),
the Python `transform()` API, and the extension registries. A consolidation that leaves the
docstring untouched leaves an unmanaged drift surface flowing through an existing export, so this
RFC's sourcing rule covers it (Deliverable 1).

## Deliverable 1 — the Language Reference document (R-34)

A new `docs/LANGUAGE.md`: the Transon **template language reference**, addressed to template
authors (human or agent), containing semantics only:

- The marker: rule invocation shape, literal-marker escaping, marker inheritance across `include`.
- Context: `this`/`item`/`key`/`index`/`parent`, variable scoping (`set`/`get`), scope derivation.
- `NO_CONTENT`: the propagation **model** — what the sentinel means, the skip-don't-emit
  principle for containers, defaults, top-level conversion. Which exact behavior a given rule
  applies is that rule's docstring's job (ownership principle below); the model section may
  cite rules as illustrations.
- Error taxonomy **as an author experiences it**: what raises `DefinitionError` vs
  `TransformationError`, with representative messages.
- Expression & call machinery: the semantics shared across **all** operators and functions —
  operator application (binary vs reduce, reduction over lists including the empty-list case),
  type coercion, `call` input/output conventions, `NO_CONTENT` interaction. Boundary: these
  facts span the whole operator/function domain, so they are cross-cutting even though they
  attach to the `expr`/`call` rules; the `expr`/`call` docstrings state their own parameter
  modes and **defer** application semantics to these sections (a deliberate pointer, the one
  place a docstring links into the reference instead of owning the fact).
- **No per-entity sections.** `LANGUAGE.md` contains no per-rule, per-operator, or per-function
  reference — that prose lives in the registration docs and is already exported to every
  consumer (see the ownership principle below). Entity names appear here only as illustrations
  of cross-cutting behavior. This keeps the document **stable**: it changes when the language
  model changes, not when the catalog grows.
- Composition patterns: chaining, `include`, the aggregate-from-primitives recipes (reduce-count,
  flatten via `map`/`items`, and their empty-list caveats).

**Sourcing rule — move, don't copy.** `LANGUAGE.md` is assembled by *relocating* every existing
copy of the language semantics, not by writing a fresh parallel one. One source of truth per
fact — two hand-maintained descriptions of `NO_CONTENT` will diverge, and today there are three:

- **`SPECIFICATION.md` §2/§11** — the cross-cutting language content is relocated into
  `LANGUAGE.md`; **§4's per-rule facts are relocated into the rule docstrings** (see the
  ownership principle), and §4 shrinks to a pointer at the generated reference. The spec keeps
  the engine-contract material and links out for semantics. §5's "nothing is hand-maintained
  separately" claim is reworded to name `LANGUAGE.md` as the one hand-written artifact.
- **The `Transformer` class docstring** — its language sections ("Templates", "How evaluation
  works", the language half of "What you can do") are relocated. The docstring shrinks to
  embedder-facing content only: a short orientation paragraph, Python API usage, "Extending", and
  a pointer to the reference. `get_all_docs()['doc']` keeps its shape and now carries this
  slimmed narrative — the docs site repurposes it for an "embedding" page.
- **`README.md`** — becomes the sole owner of the pitch ("What is transon?", the comparisons,
  install); the docstring's copies of those sections are dropped. The docs site builds its
  landing from README at build time (docs-site work, see Sequencing), not from the docstring.

**Ownership principle — one owner per altitude.** Every fact has exactly one home, chosen by
its altitude; every channel composes these sources (joined by entity name, the same name-join
the corpus normalization R-31 established) and none restates another:

- **Structure** — parameter names, required-ness, modes/variants, dynamic-vs-constant kinds,
  containers, operator/function types: the registration metadata, exported as the
  `get_editor_metadata()` catalog. Never restated as prose tables anywhere.
- **Per-entity behavior** — what one rule/operator/function does, its modes, its edge cases
  (empty input, missing keys, `NO_CONTENT` handling): the registration docs — rule docstrings
  and `doc=` kwargs. This channel already reaches every consumer: the docs site renders its
  per-rule pages from it, the editor shows it as help text, and the authoring snapshot carries
  it (`get_editor_metadata()['docs']`). The deeper per-rule facts currently in
  `SPECIFICATION.md` §4 are **relocated into the docstrings**, which grow richer — the existing
  no-`TBD` gate and docs tests keep guarding them.
- **Cross-cutting semantics** — the evaluation model, scoping, `NO_CONTENT` propagation across
  containers, the error taxonomy, `expr`/`call` machinery, composition patterns: `LANGUAGE.md`.
  Facts that span entities have no docstring to live in; this narrative is exactly what no
  export carries today.
- **Examples** — the corpus, referenced by name from everything else (unchanged).

Volatility follows ownership: adding or changing a rule/function touches `rules.py` (and the
corpus) only; `LANGUAGE.md` changes only when the language model itself changes.

**API prose split.** `SPECIFICATION.md` §3 remains the *stability contract* for the Python API
(what is stable across versions, what subclassing must preserve, registry resolution order);
*usage* prose lives in the docstrings. Neither restates the other.

**Drift protection.** `LANGUAGE.md`'s topical section ids are **pinned** in a deterministic
test (alongside `tests/test_docs.py` / `tests/test_metadata.py`): the expected section list is
explicit, so adding, renaming, or removing a section is a conscious act tied to the
`reference_version` policy (Deliverable 3) — never silent. There is **no** catalog-coverage
check against `LANGUAGE.md`: per-entity coverage is the registration docs' job, already guarded
by the existing no-`TBD` gate and docs-shape tests, and `LANGUAGE.md` has no per-entity headings
to drift. The prose stays hand-written.

## Deliverable 2 — ship the reference in the package (R-35)

`LANGUAGE.md` becomes package data (e.g. `transon/resources/LANGUAGE.md`, included in the wheel
and sdist), so an installed `transon==<version>` serves its own language reference offline —
exactly the property `get_editor_metadata()` already has for the catalog. The repo-root
`docs/LANGUAGE.md` stays the canonical, human-edited source; the build maps it in (mirroring the
`transon-authoring` `resources/` force-include pattern) or a release check asserts the two are
identical.

**Acceptance (packaging parity).** A test loads the packaged `LANGUAGE.md` through
`importlib.resources` — exercising the installed wheel/sdist layout, not just the source tree —
decodes those bytes as UTF-8, normalizes line endings to `\n`, and asserts the result equals
`get_language_reference()['content']` (which is UTF-8 text with `\n` newlines), following the
shape-test pattern in `tests/test_metadata.py`. This catches a missing package-data glob or a stale
packaged copy, neither of which the section-pin test (Deliverable 1) would notice.

## Deliverable 3 — `get_language_reference()` export (R-36)

A read-only export, separate from the docs API, mirroring the `get_editor_metadata()` conventions:

- `transon.reference.get_language_reference()` → the document, versioned:

```json
{
  "reference_version": "<schema version>",
  "engine_version": "<package version>",
  "format": "markdown",
  "content": "<the full LANGUAGE.md text>",
  "sections": [
    {"id": "no-content", "title": "NO_CONTENT", "heading_level": 2, "content": "..."},
    ...
  ]
}
```

- `sections` is a flat, ordered split of `content` by heading, each with a stable slug `id`, so
  consumers can serve **targeted** section lookups (a 700-line dump into an agent context is the
  failure mode; one section is the unit of consumption). `content` is the byte-exact document for
  consumers that want the whole thing.
- **Splitting rules** (deterministic): the split is on top-level `##` headings only, so `sections`
  is flat, not a tree. Each section runs from its `##` heading up to the next `##` heading and
  **includes its own heading line**; any deeper (`###`+) heading stays inside its parent section.
  Content before the first `##` heading (the intro under the `#` title) becomes a leading preamble
  section — present **only when that intro is non-empty** — carrying
  `{"id": "preamble", "title": "", "heading_level": null, ...}`. Every other section carries
  `heading_level: 2` and the heading's text as `title`. `id` is the GitHub-style slug of the heading
  text (the preamble's is the literal `"preamble"`); a collision gets a `-2`, `-3`, … suffix in
  document order, so `id`s are unique and stable. A parity test asserts the concatenation of
  `sections` (in order) reproduces `content`.
- **`reference_version` policy** (mirrors `METADATA_VERSION` and the [RFC 0001](0001-editor-metadata-export.md)
  versioned-export conventions): additive changes — a new section, appended prose, a new optional
  field — bump the **minor**; removing or renaming a section `id`, changing the `sections` shape, or
  dropping/renaming a top-level field is **breaking** and bumps the **major**. A consumer that reads
  an unsupported major MUST fail its drift check loudly (as `transon-authoring`'s `check_snapshot.py`
  already does for the metadata pin) rather than silently serve stale semantics.
- `python -m transon.reference` prints the JSON (parallel to `python -m transon.docs` and
  `python -m transon.metadata`).
- The export states **language facts only** — no consumer-specific shapes (no skill procedure, no
  editor widgets), same line as metadata-contract §2.8.
- The export is **engine-global**: it documents the built-in language of the base `Transformer`
  only. Unlike `get_all_docs(cls=...)`, there is no class parameter — rules registered on
  subclasses are outside the reference.

Consumers then pin it like they pin the metadata: `transon-authoring` bundles the export at its
engine pin, syncs it in `scripts/sync_metadata.py`, drift-checks it in `scripts/check_snapshot.py`,
and serves it via a new CLI lookup (`spec search` / `spec --section`) — that half is a SPEC-first
change in the `transon-authoring` repo, out of scope here.

## Sequencing

All three deliverables **plus** the docstring/README consolidation land atomically in one
release: at no point is a language fact absent from every published surface, and the docs site
migrates against a single version. The docs-site counterpart (render `LANGUAGE.md`, build the
landing from `README.md`, absorb the slimmed `doc` field as the embedding page) is **D-20** in
`docs/DOCS_SITE_ROADMAP.md` — it is a **dependency** of this
release, not an option, because the slimmed docstring removes the narrative the site renders
today. The `CHANGELOG.md` entry for the release names the `get_all_docs()['doc']` content change
explicitly.

## Non-goals

- **No behavior change**: no template semantics move; this is documentation + packaging + a
  read-only accessor.
- **No second source of truth**: content is moved out of `SPECIFICATION.md` (§2/§11 to the
  reference, §4 to the docstrings), the `Transformer` docstring, and `README.md` — never
  duplicated; the section-pin test guards the reference's shape, the no-`TBD` gate guards the
  registration docs.
- **No generated prose**: rule *examples* stay generated and normalized in the corpus (§5, R-31);
  `LANGUAGE.md` references behavior, it does not re-serialize examples. (How the docs site
  *renders* `LANGUAGE.md` is docs-site work — D-20, see Sequencing — but rendering
  it is a release dependency, not a later option.)
- **No audience fan-out**: one author-facing reference. Separate authoring/running/validating
  documents multiply drift surfaces; "running" (embedding the engine, the `transform()` API)
  stays with the code — usage in docstrings, stability contract in `SPECIFICATION.md` §3.

## Cross-repo provenance

- Consumer contract: `transon-authoring/SKILL.md` Authority ladder (rung 2), AD-018 / NFR-001 /
  NFR-003 (offline grounding); its snapshot-pin machinery (`scripts/sync_metadata.py`,
  `scripts/check_snapshot.py`, `resources/metadata-snapshot.*`) is the pattern this export plugs
  into.
- Secondary consumer: `transon-blockly` docs/help surfaces may link section ids for rule help
  text, but the editor contract (`metadata-contract.md`) is unchanged by this RFC. Rule
  docstrings grow richer as §4's per-rule facts fold in; the contract treats doc text as opaque,
  so no shape change — how much of it the editor displays (tooltip vs. help panel) is
  editor-owned presentation.
- Docs site (`transon-org.github.io`): **depends on this release** — renders `LANGUAGE.md`,
  sources its landing from `README.md` at build time, and absorbs the slimmed
  `get_all_docs()['doc']` as the embedding page (see Sequencing).
- Prior art in this repo: [RFC 0001](0001-editor-metadata-export.md) (R-24) — the
  versioned-export conventions this RFC copies.
