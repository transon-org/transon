# RFC 0007 — Grow the built-in function library (string / numeric / collection helpers)

- **Status:** Implemented — pending 0.2.0 packaging (held with RFC 0008)
- **Created:** 2026-07-16
- **Roadmap:** R-33 (`done`) — targets a **0.2.0** minor release (with RFC 0008)
- **Type:** Additive engine capability — every addition is a newly-named function/operator/rule; no behavior change to existing templates
- **Consumers:** `transon-authoring` (skill; pins the registry snapshot), `transon-blockly` (optional membership-predicate follow-up)
- **Supersedes / Superseded by:** — / —

> **Context.** No code yet; this RFC exists to get the scope and per-function semantics decided before
> implementation, as the roadmap policy requires for additive-but-published surface. Direct
> continuation of [RFC 0002](0002-type-function.md) (R-26): that added the one primitive the
> projection codec needed (`type`); this RFC addresses the opposite pressure — **authoring**
> ergonomics — with a batch of ordinary value functions. No new transformation language; no
> path/expression DSL.

## Why

Transon 0.1.7 ships **four** functions — `str`, `int`, `float`, `type` ([`transon/functions.py`]) —
and 14 operators. That set is deliberately minimal and structurally complete for *transformation*,
but it forces two recurring costs that the downstream **`transon-authoring`** skill has measured
directly against real payloads (AWS EC2, Stripe, GitHub) while building its eval corpus:

**1. Genuine capability gaps.** Some transformations simply cannot be expressed and become
*refusals*. The authoring corpus has three standing "refuse" fixtures that exist **only** because the
engine cannot do the work:

| Refuse fixture (authoring corpus) | What the input needs | Why it's impossible today |
|---|---|---|
| epoch → ISO timestamp | `1712345678` → `"2024-04-05T18:14:38Z"` | no date/time function at all |
| uppercase currency code | `"usd"` → `"USD"` | no string-case function |
| strip `refs/heads/` prefix | `"refs/heads/main"` → `"main"` | no substring / prefix operation |

These are not exotic asks — they are the first things a real webhook or resource payload demands.

**2. Idioms that *work* but are verbose and turn-expensive.** Aggregations are expressible via
`map` + `expr` `values` reduction, but every one is multi-node boilerplate repeated at each call
site, and several have sharp edges:

- **count** = `map`(→`1`) then `expr` `values` reduce `+` — and `expr` `values` **raises
  `DefinitionError` on an empty list** ([`transon/rules.py`], the `values` guard), so every
  aggregate needs an empty-input guard around it.
- **flatten / concat** of a dynamic list-of-lists = the same reduce trick with `+`.
- **length of a string/array/object** has no direct form.

The authoring eval transcripts show hard fixtures (`ec2-flatten-inventory`) exhausting their entire
tool-turn budget largely on drafting this class of boilerplate. A small, well-chosen function batch
turns three refusals into capabilities and collapses the common idioms to one node.

This is the natural next increment for the same reason `type` was: an ordinary function is purely
additive, carries its own docs into `get_editor_metadata()` / `get_functions_docs()`, needs no new
language, and cannot change the meaning of any existing template.

## Design constraints (these bound the list more than taste does)

These are hard invariants for anything added here; they are why several "obvious" functions are
**declined** below.

1. **Pure and deterministic (this rule is absolute).** Every downstream contract assumes *same
   template + same input → same output, forever*: the `transon-blockly` codec projections, and the
   `transon-authoring` `verify()`/`matched` check plus its engine-frozen eval fixtures. Therefore
   **no** `now()`, `today()`, `random`, `uuid`, `env`, or any I/O. Anything date-shaped must
   transform a value **taken from the input**, never read a wall clock. No locale-dependent
   behavior; date formatting is fixed (ISO-8601, UTC) or takes an explicit format string. (This
   governs *determinism*, not error-raising: a function may still raise a transon error on bad
   input — that is constraint 3's domain.)

2. **Multi-argument is already free.** The `call` rule's `values` mode evaluates
   `function(*values)` ([`transon/rules.py`], `rule_call`), and `int`'s optional base argument is the
   existing precedent. So `split`, `replace`, `round`, `removeprefix`, … need **no rule/plumbing
   change** — only a `register_function`.

3. **Errors must stay inside the transon error model (R-02).** `rule_call`'s wrapper catches
   `TypeError` and re-raises transon errors, **but nothing else** — a function that raises
   `ValueError` (e.g. `min([])`, `int("nope")`-style, `sorted` on mixed types → `TypeError` *is*
   caught, but `ValueError` is not) would escape as a raw Python exception, the exact defect R-02
   closed. So every function added here must **either** be total, **or** take an explicit `default`
   (supplied via `values`), **or** raise a transon `TransformationError`/`DefinitionError` itself —
   never let a bare `ValueError` through. This is a per-function requirement, not a nicety.

4. **Docs are the product.** `register_function(..., doc=…)` populates `get_functions_docs()` and
   `get_editor_metadata()`, which is the snapshot the editor pins and the `transon-authoring` skill
   grounds on. Each new function **must** ship a `doc` plus at least one entry in the flat example
   corpus (referenced via `get_example_names_for_function`), or it is invisible to both the editor
   enum and the authoring model. A function without an example is not done.

5. **Naming follows the stdlib flavor** already set by `str`/`int`/`float`/`type`: `upper`, `split`,
   `replace`, `length`, `sum`. Document totality or the exact raised error the way `type`'s doc
   documents its totality.

## Proposed additions

Grouped by confidence. Recommendation is **Tier 1 + the count/flatten/length subset of Tier 2** for
0.2.0; the rest rides a follow-up once the downstream adversarial corpus is restocked (see
Downstream).

### Tier 1 — close the measured capability gaps (**recommended, required for 0.2.0**)

Each of these turns a standing refusal into a capability.

| Function | Invocation | Output | Semantics / totality |
|---|---|---|---|
| `upper`, `lower` | unary | str | total on strings; non-str input is a `TransformationError` (document it) |
| `split` | `values: [s, sep]` | array | the missing inverse of the existing `join` **rule**; `sep` required (no whitespace-magic default) |
| `replace` | `values: [s, old, new]` | str | total; covers many prefix/suffix cases |
| `removeprefix`, `removesuffix` | `values: [s, fix]` | str | the **correct** fix for `refs/heads/` — `lstrip` would wrongly eat leading characters, not a prefix |
| `strip`, `lstrip`, `rstrip` | unary, or `values: [s, chars]` | str | character-set trimming; explicitly **not** a substitute for `removeprefix` |
| `from_epoch` | unary (number) | str | epoch **seconds** → ISO-8601 UTC (`YYYY-MM-DDThh:mm:ssZ`), fixed format, pure; a non-numeric input raises `TransformationError` |
| `format_epoch` | `values: [n, fmt]` | str | epoch seconds + explicit format; UTC only. **Locale-free directives only** — restricted to a whitelist (`%Y %m %d %H %M %S %j %z` + literal text); locale-sensitive directives (`%a %b %c %x %X %p`) and `%Z` are rejected with a `TransformationError`, so output stays deterministic across hosts |

> **Date scope is deliberately narrow.** Only epoch-based, because epoch is unambiguous and
> locale-free. General `parse_date(s, fmt)` is listed under Tier 3 — parsing arbitrary strings drags
> in timezone/locale ambiguity that fights constraint 1 and needs its own decision.

### Tier 2 — replace the reduce idioms (**recommend the count/flatten/length subset now**)

| Function | Invocation | Output | Notes / empty-input rule (constraint 3) |
|---|---|---|---|
| `length` | unary | int | total over string/array/object; kills the `map`(→1)+reduce count idiom. **Recommended.** |
| `flatten` | unary (array of arrays) | array | one level only; the other reduce idiom. Non-array element → `TransformationError`. **Recommended.** |
| `sum` | unary (array) | number | `sum([])` = `0` (total). **Recommended** alongside `length`. |
| `min`, `max` | `values: [array]` or `[array, default]` | any | **empty array MUST be handled** — either require `default` or raise `TransformationError`, never a bare `ValueError` |
| `sorted`, `reversed`, `unique` | unary (array) | array | `sorted` on **mixed scalar types raises `TypeError`** in Py3 (→ caught → `TransformationError`); restrict/document to homogeneous scalars |
| `contains` | `values: [container, item]` | boolean | membership; today needs `filter`+length. **Should be total** (no throw on absent/empty) — the one editor-facing lever (see Downstream → `transon-blockly`); a `has(obj, key)` operator is a tighter alternative shape |
| `abs`, `round`, `floor`, `ceil` | unary; `round` = `values: [x, ndigits]` | number | numeric hygiene |
| `bool` | unary | boolean | completes the `str`/`int`/`float`/`bool` conversion family; pairs with `type` in `switch` keys |

### Tier 3 — defer to a separate decision (listed so they are not silently forgotten)

- `parse_date(s, fmt)` — arbitrary-string date parsing; timezone/locale ambiguity vs constraint 1.
- `json_parse` / `json_dump` — string↔structure; changes what "value" means at a boundary.
- `regex_match` / `regex_replace` — **the single biggest real-payload ask**, but brings ReDoS
  exposure and dialect-portability questions (the projected editor/Pyodide host must agree on the
  regex engine). **Proposed as its own RFC**, not bundled here.
- `urlencode` / `base64` / zero-padding number formatting beyond the `format` rule.

### Explicitly out of scope (declined — violate constraint 1)

`now()`, `today()`, `random`, `uuid`, `env`, file/network I/O. Each breaks the determinism the
codec projections and the authoring `verify()`/engine-frozen fixtures depend on. A template that
reads a clock or entropy source is unverifiable by construction — non-negotiable.

## Downstream implications (why this is a coordinated change, not a drop-in)

### `transon-authoring` (skill)

The `transon-authoring` skill pins this engine and its registry snapshot as its normative contract,
so a 0.2.0 bump is a governed change on that side, not a silent upgrade:

1. **The three Tier-1 refuse fixtures flip from "refuse" to "matched."** The authoring corpus must
   **restock its adversarial bucket** with capabilities that remain genuinely absent (e.g. `regex`,
   `now()`, cross-record joins) so the refusal target keeps measuring a real boundary rather than a
   closed gap.
2. **New `docs.examples` per function feed the authoring fixture generator** — its synthetic-fixture
   generator mints coverage from the metadata snapshot, so registering docs+examples (constraint 4)
   grows downstream coverage for free.
3. **Corpus + engine change ⇒ the downstream eval baseline resets** and needs a fresh full green
   gate before it can be re-accepted. That is a real, budgeted cost on the authoring side; sequencing
   the engine release so the authoring repo can absorb it in one governed pass matters.

None of this blocks the engine release — it is the *consumer's* follow-up — but the RFC records it so
the flip is planned rather than discovered.

### `transon-blockly` (editor) — a total membership predicate could shrink the generators

> **Ownership note: this is a `transon-blockly` follow-up, not an R-33 deliverable.** It adds **no**
> engine requirement, task, or test here, and does not gate this release. It is recorded only so that
> *if* a membership predicate is included in the function/operator set, its **totality** is decided
> with this editor use in mind. The generator refactor itself is designed and tracked in the editor
> repo, later.

The editor's committed codec generators (`G_encode` / `G_decode`, themselves Transon templates run
with the meta-marker `@`) repeat one verbose idiom: an **optional-key existence check** built from a
sentinel `join` default plus an `expr !=` compare — roughly six sites (e.g.
`transon-blockly` `G_decode.json` ~L129–180, and the `transon::absent-key` markers in `G_encode.json`).
Each spends ~1 map + 1 filter + 1 join + 1 expr computing what is simply *"does this object contain
key K"*:

```
chain: get obj → attr fields → map item:key        # all keys
     → filter cond: key == K                         # keep matches
     → join sep:"," default:"transon::absent-key"    # empty ⇒ sentinel
expr != [ joined , "transon::absent-key" ]           # ⇒ boolean membership
```

A **total** membership predicate — `contains(container, item)` (Tier 2) as a function, or a
`has(obj, key)` / `in` operator — collapses each site to a single node and lets the generators drop
the whole `map`+`filter`+`join`+`expr` scaffold.

**Totality is the load-bearing property**, and the only thing this note asks the engine decision to
account for: the sentinel idiom exists *because* `attr` on a missing key throws, and a `switch`/`cond`
key must never throw — exactly the constraint that motivated `type` (R-26). A throwing membership op
cannot replace the idiom. So a `contains`/`has` intended for this use must be **total** (constraints 1
and 3), documented like `type`'s totality.

Note the flip side: the string/date/aggregation functions in this RFC do **not** shrink the
generators — the projections only ever *compose* strings (`transon_rule_<name>__<id>`) and dispatch on
the whole built key, never decompose them; and the generators carry no count/flatten/reduce idiom
(`length`/`sum`/`flatten` are authoring-side wins). The membership predicate is the one editor-facing
lever, which is why its totality is worth deciding deliberately rather than by accident.

## Requirements (if accepted)

- Register each accepted function in [`transon/functions.py`] with `input_type` / `output_type` /
  `doc`, following the `str`/`int`/`float`/`type` pattern; multi-arg ones rely on `call` `values`
  (no rule change).
- **Per-function empty/error audit against constraint 3** — prove no bare `ValueError`/`KeyError`
  escapes `rule_call`'s `TypeError`-only guard; add an explicit transon error or `default` where it
  would.
- **Boundary contracts pinned per function** (part of that audit, each with a test): `split` — empty
  `sep` raises a `TransformationError`, not Python's `ValueError`; `from_epoch` / `format_epoch` —
  state the accepted numeric range and rounding/precision (fractional seconds truncated vs rounded),
  and normalize non-finite (`NaN`/`inf`) or out-of-range inputs to a `TransformationError`, never a
  raw `ValueError`/`OverflowError`/`OSError`; `format_epoch` — reject any non-whitelisted directive
  (see the Tier-1 note) rather than emit locale-dependent text.
- One flat-corpus example per function (`get_example_names_for_function` must resolve), so the editor
  enum and the authoring snapshot both pick it up.
- `SPECIFICATION.md` function section updated; **changelog** entry under a new `## [0.2.0]` (additive,
  loud — new published surface), **minor version bump**.
- Tests: one per function covering the happy path, the documented error/empty behavior, and metadata
  presence (`get_functions_docs()` lists it).
- Roadmap: flip R-33 status and record the decided scope (which tiers landed).

## Open decisions for the maintainer

1. **Scope for 0.2.0** — the recommended cut (Tier 1 + `length`/`flatten`/`sum`), or wider/narrower.
2. **`min`/`max`/`sorted` empty & mixed-type policy** — require `default`, or raise a documented
   `TransformationError`? (Constraint 3 forbids doing nothing.)
3. **Date surface** — epoch-only (`from_epoch`/`format_epoch`) for 0.2.0, with `parse_date` and
   regex each deferred to their own RFC? (Recommended.)
4. **Release shape** — one 0.2.0 with the whole recommended batch, or split Tier 1 (0.2.0) from the
   Tier-2 subset (0.2.1)?

[`transon/functions.py`]: ../../transon/functions.py
[`transon/rules.py`]: ../../transon/rules.py
