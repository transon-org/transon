# Transon RFCs

Design proposals ("RFCs") for the Transon engine. Each RFC is one numbered Markdown file that
motivates a change, records the decision and the alternatives weighed, and states what shipping it
requires. RFCs are the *narrative* home of a change; the [`docs/ROADMAP.md`](../ROADMAP.md) tracker
is the *authoritative* record of each work item's status via its **R-number**.

## How the process works

- **One decision, one RFC.** An RFC exists to get a scope + semantics decision made before
  implementation (or to document a decision already made). It is written to be read on its own.
- **RFCs map to roadmap R-numbers, not 1:1.** A single RFC often delivers several roadmap items
  (RFC 0001 → R-23/R-24/R-25). The R-number is the unit of *tracking and status*; the RFC is the
  unit of *design*. The `Roadmap:` field in each RFC header names its R-numbers, and each roadmap
  entry links back to its `Source:` RFC.
- **The roadmap is authoritative for outcome.** An RFC body is preserved as written at proposal
  time (it may read in future tense even after shipping). Its **`Status`** header field and its
  roadmap R-number(s) — including the roadmap's *Shipped* notes — are the source of truth for what
  actually happened.
- **Consumers are coordinated, not silent.** Most RFCs here are engine-side counterparts of
  downstream work in `transon-blockly`, `transon-authoring`, or the docs site. The `Consumers:`
  field names them; the RFC's *Cross-repo provenance* section carries the contract pointers.

## Status lifecycle

| Status | Meaning | Roadmap term |
|---|---|---|
| **Proposed** | Open for a decision; no code yet (or scope not finalized). | `needs-decision` |
| **Accepted** | Decision made; awaiting implementation. | `accepted` |
| **Implemented** | Shipped in a release (the `Status` line names the version). | `done` |
| **Rejected** | Decided against; kept for the record. | `rejected` |
| **Deferred** | Postponed pending a trigger stated in the RFC. | — |
| **Superseded** | Replaced by a later RFC (named in `Superseded by`). | — |

## Index

| # | Title | Status | Roadmap | Shipped | Consumers |
|---|---|---|---|---|---|
| [0001](0001-editor-metadata-export.md) | Editor-metadata export + projection-support rules | Implemented | R-23, R-24, R-25 | v0.1.1–0.1.2 | `transon-blockly` |
| [0002](0002-type-function.md) | `type` value-type function (+ `include` loader propagation) | Implemented | R-26, R-27 | v0.1.3 | `transon-blockly` |
| [0003](0003-editor-metadata-structural-params.md) | Export structural param facts (`container` + `arm`) | Implemented | R-28 | v0.1.4 | `transon-blockly` |
| [0004](0004-editor-metadata-example-tiers.md) | Export example tags + curated example tiers | Implemented | R-29, R-30 | v0.1.5 | `transon-blockly` |
| [0005](0005-example-corpus-normalization.md) | Normalize exports to one flat example corpus | Implemented | R-31 | v0.1.6 | docs site, `transon-blockly` |
| [0006](0006-transformer-recursion-depth-budget.md) | Bounded per-level recursion budget (self-`include` depth) | Implemented | R-32 | v0.1.7 | `transon-blockly` |
| [0007](0007-builtin-function-library.md) | Grow the built-in function library | Implemented | R-33 | v0.1.8 | `transon-authoring`, `transon-blockly` |
| [0008](0008-language-reference-export.md) | Author-facing Language Reference: doc, packaging, export | Accepted | R-34, R-35, R-36 | — | `transon-authoring`, docs site |

## Adding a new RFC

1. **Claim the next number.** RFCs are numbered sequentially, zero-padded to four digits
   (`0009-…`). Numbers are permanent and never reused.
2. **Claim the next roadmap R-number(s)** in [`docs/ROADMAP.md`](../ROADMAP.md) for the work items —
   one per independently-trackable deliverable — and reference them in the header. (R-numbers are a
   single global sequence; do not reuse one already listed above.)
3. **Name the file** `NNNN-short-kebab-slug.md`.
4. **Start with the standard header**, then the body (`## Why`, deliverables, `## Non-goals`,
   `## Cross-repo provenance`, out-of-scope):

   ```markdown
   # RFC NNNN — <title>

   - **Status:** Proposed — `needs-decision`
   - **Created:** <YYYY-MM-DD>
   - **Roadmap:** R-NN (<label>) — <roadmap term>
   - **Type:** <additive | shape-breaking | fix; behavior impact on existing templates>
   - **Consumers:** <downstream repos + contract pointers, or "none">
   - **Supersedes / Superseded by:** — / —

   > **Context.** <one-paragraph framing: what pressure this answers, and which repo/contract it
   > is the counterpart of>
   ```

5. **Add a row to the index** above and a `Source:` link from each roadmap entry back to the RFC.
