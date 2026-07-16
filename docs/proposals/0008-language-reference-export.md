# RFC 0008 — Author-facing Language Reference: document, packaging, and export API

- **Status:** Proposed
- **Created:** 2026-07-16
- **Roadmap:** R-34 (Language Reference document), R-35 (package the reference), R-36 (`get_language_reference()` export) — proposed; add rows to `docs/ROADMAP.md` on acceptance. (R-33 is held by [RFC 0007](0007-builtin-function-library.md).)
- **Type:** New documentation artifact + packaging + a read-only export API — additive; no behavior change to any template or engine API
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
reference), and §11 (data flow), interleaved with the rest.

Two consumers need the language half, by itself, offline, pinned to an engine version:

1. **`transon-authoring`** — its agents ground drafts in the metadata snapshot (examples show
   *structure*) and the verify gate (pass/fail shows *behavior*), but have nothing that explains
   *semantics*: `NO_CONTENT` propagation, `DefinitionError` vs `TransformationError`, mode
   selection, empty-list `expr` reduction. Repair loops burn their bounded budget rediscovering
   facts a reference section would state. The skill's harnesses mount no repo checkout, so the
   document must travel inside the installed package, like the metadata snapshot does.
2. **Human authors / the docs site** — the playground and docs site currently render generated
   example JSON; a coherent authoring narrative has no source document.

Shipping `SPECIFICATION.md` itself is the wrong fix: it tells an authoring agent about extension
registries and subclassing (capabilities outside the authoring profile) and about open design
questions — content an author must not act on.

## Deliverable 1 — the Language Reference document (R-34)

A new `docs/LANGUAGE.md`: the Transon **template language reference**, addressed to template
authors (human or agent), containing semantics only:

- The marker: rule invocation shape, literal-marker escaping, marker inheritance across `include`.
- Context: `this`/`item`/`key`/`index`/`parent`, variable scoping (`set`/`get`), scope derivation.
- `NO_CONTENT`: where it is produced, how each container rule treats it, top-level behavior.
- Error taxonomy **as an author experiences it**: what raises `DefinitionError` vs
  `TransformationError`, with representative messages.
- Per-rule reference: every built-in rule with its parameters, modes/variants, and edge-case
  behavior (empty input, missing keys, `NO_CONTENT` items) — plus operators and functions.
- Composition patterns: chaining, `include`, the aggregate-from-primitives recipes (reduce-count,
  flatten via `map`/`items`, and their empty-list caveats).

**Sourcing rule — move, don't copy.** The language content of `SPECIFICATION.md` §2/§4/§11 is
*relocated* into `LANGUAGE.md`; `SPECIFICATION.md` keeps the engine-contract material and links to
the reference for semantics. One source of truth per fact — two hand-maintained descriptions of
`NO_CONTENT` will diverge.

**Drift protection.** A deterministic parity test (alongside `tests/test_docs.py` /
`tests/test_metadata.py`) asserts that every rule, parameter, operator, and function in the
`get_editor_metadata()` catalog has a matching heading/anchor in `LANGUAGE.md`, and that no
reference section names a catalog entry that does not exist. The prose stays hand-written; the
*coverage* is machine-checked, the same way the corpus invariants are.

## Deliverable 2 — ship the reference in the package (R-35)

`LANGUAGE.md` becomes package data (e.g. `transon/resources/LANGUAGE.md`, included in the wheel
and sdist), so an installed `transon==<version>` serves its own language reference offline —
exactly the property `get_editor_metadata()` already has for the catalog. The repo-root
`docs/LANGUAGE.md` stays the canonical, human-edited source; the build maps it in (mirroring the
`transon-authoring` `resources/` force-include pattern) or a release check asserts the two are
identical.

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
- `python -m transon.reference` prints the JSON (parallel to `python -m transon.docs` and
  `python -m transon.metadata`).
- The export states **language facts only** — no consumer-specific shapes (no skill procedure, no
  editor widgets), same line as metadata-contract §2.8.

Consumers then pin it like they pin the metadata: `transon-authoring` bundles the export at its
engine pin, syncs it in `scripts/sync_metadata.py`, drift-checks it in `scripts/check_snapshot.py`,
and serves it via a new CLI lookup (`spec search` / `spec --section`) — that half is a SPEC-first
change in the `transon-authoring` repo, out of scope here.

## Non-goals

- **No behavior change**: no template semantics move; this is documentation + packaging + a
  read-only accessor.
- **No second source of truth**: language sections are moved out of `SPECIFICATION.md`, not
  duplicated; the parity test guards catalog coverage, not prose duplication.
- **No generated prose**: rule *examples* stay generated and normalized in the corpus (§5, R-31);
  `LANGUAGE.md` references behavior, it does not re-serialize examples. (Whether the docs site
  later renders `LANGUAGE.md` is a `DOCS_SITE_ROADMAP.md` concern.)
- **No audience fan-out**: one author-facing reference. Separate authoring/running/validating
  documents multiply drift surfaces; "running" (embedding the engine, `transform()` API) stays in
  `SPECIFICATION.md` §3.

## Cross-repo provenance

- Consumer contract: `transon-authoring/SKILL.md` Authority ladder (rung 2), AD-018 / NFR-001 /
  NFR-003 (offline grounding); its snapshot-pin machinery (`scripts/sync_metadata.py`,
  `scripts/check_snapshot.py`, `resources/metadata-snapshot.*`) is the pattern this export plugs
  into.
- Secondary consumer: `transon-blockly` docs/help surfaces may link section ids for rule help
  text, but the editor contract (`metadata-contract.md`) is unchanged by this RFC.
- Prior art in this repo: [RFC 0001](0001-editor-metadata-export.md) (R-24) — the
  versioned-export conventions this RFC copies.
