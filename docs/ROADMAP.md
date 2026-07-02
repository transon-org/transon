# transon — Improvement roadmap

> **Status of this document**: living backlog. Every entry follows the same format:
> problem → impact of not fixing → options (with a recommendation when one option is
> clearly better). Behavior-changing items must not be implemented silently — they
> need an explicit decision recorded here (flip the status) and a changelog entry,
> because published templates may rely on current behavior.
>
> Sources: the spec's former §12 "Known issues" list — **fully migrated into this
> file**; per-item `Spec: §12.N` labels record which original entry an item came
> from — plus an engine-semantics audit (2026-06, labeled `Source: audit`). All
> described behaviors are verified against the implementation (v0.0.9).

**Statuses**: `needs-decision` (maintainer must pick an option) ·
`accepted` (option chosen, ready to implement) · `in-progress` · `done` ·
`rejected` (decided to keep current behavior — record why).

## Policy decisions (recorded 2026-06-13)

1. **Compatibility**: pre-1.0 freedom — behavior-changing fixes may change defaults
   directly, with a changelog entry and a minor version bump. No opt-in flags
   required for compatibility's sake alone. This unblocks the breaking-change
   concern in ~~R-01~~ (done), ~~R-02~~ (done), ~~R-06~~ (done), ~~R-07~~ (done), ~~R-11~~ (done) (each still needs its per-item option
   chosen, but "is breaking acceptable" is settled: yes, with changelog).
2. **Python versions**: ~~R-20~~ (done) — require ≥3.9, CI 3.9–3.13, uv for packaging;
   `importlib-metadata` backport and 3.7 compat rules retired.

## Checklist

| ID | Title | Severity | Status |
|---|---|---|---|
| [R-01](#r-01-andor-operators-are-bitwise-not-logical) | `and`/`or` operators are bitwise, not logical | high | done |
| [R-02](#r-02-raw-python-exceptions-escape-the-error-model) | Raw Python exceptions escape the error model | high | done |
| [R-03](#r-03-reserved-name-guard-is-an-assert-vanishes-under--o) | Reserved-name guard is an `assert` — vanishes under `-O` | high | done |
| [R-04](#r-04-no-template-validation-phase-typos-and-ambiguity-pass-silently) | No template validation; typos and ambiguity pass silently | high | done |
| [R-05](#r-05-error-messages-carry-no-template-location) | Error messages carry no template location | medium | done |
| [R-06](#r-06-no_content-leaks-to-the-caller-at-top-level) | `NO_CONTENT` leaks to the caller at top level | high | done |
| [R-07](#r-07-no_content-leaks-into-format-output) | `NO_CONTENT` leaks into `format` output | high | done |
| [R-08](#r-08-join-is-inconsistent-with-no_content-items) | `join` is inconsistent with `NO_CONTENT` items | medium | done |
| [R-09](#r-09-no_content-as-a-dynamic-name-attrsetget) | `NO_CONTENT` as a dynamic name (`attr`/`set`/`get`) | medium | done |
| [R-10](#r-10-no-default-value-mechanism) | No default-value mechanism | medium | done |
| [R-11](#r-11-zip-emits-python-tuples-and-inherits-python-zip-quirks) | `zip` emits Python tuples and inherits Python `zip` quirks | medium | done |
| [R-12](#r-12-join-of-an-empty-list-returns-) | `join` of an empty list returns `""` | low | done |
| [R-13](#r-13-output-aliases-input-data-shared-mutable-structures) | Output aliases input data (shared mutable structures) | medium | done |
| [R-14](#r-14-no-escape-for-a-literal-marker-key) | No escape for a literal marker (`$`) key | medium | done |
| [R-15](#r-15-set-scoping-is-subtle-and-undocumented) | `set` scoping is subtle and undocumented | medium | done |
| [R-16](#r-16-constant-vs-dynamic-parameters-are-inconsistent) | Constant vs dynamic parameters are inconsistent | low | done |
| [R-17](#r-17-include-has-no-cycledepth-protection-and-a-non-transon-default-error) | `include` has no cycle/depth protection; default loader raises `RuntimeError` | low | done |
| [R-18](#r-18-include-rule-has-no-docstring) | `include` rule has no docstring | low | done |
| [R-19](#r-19-docs-expr-with-values-ignores-this--underemphasized) | Docs: `expr` with `values` ignores `this` — underemphasized | low | done |
| [R-20](#r-20-python-version-policy-37-is-eol-no-312313-in-ci) | Python version policy: 3.7 is EOL, no 3.12/3.13 in CI | medium | done |
| [R-21](#r-21-broken-type-annotations-in-transformerspy) | Broken type annotations in `transformers.py` | low | done |
| [R-22](#r-22-contextderive-copies-all-variables-on-every-scope) | `Context.derive` copies all variables on every scope | low | done |
| [R-23](#r-23-switch-and-cond-lazy-dispatch-rules) | `switch` and `cond` lazy-dispatch rules | medium | done |
| [R-24](#r-24-get_editor_metadata-projection-ready-export) | `get_editor_metadata()` projection-ready export | medium | done |
| [R-25](#r-25-include-default-marker-inheritance) | `include` default-marker inheritance | low | done |
| [R-26](#r-26-type-value-type-function) | `type` value-type function | medium | done |
| [R-27](#r-27-include-propagates-template_loader-through-context) | `include` propagates `template_loader` through context | medium | done |
| [R-28](#r-28-export-structural-param-facts-container--arm-in-the-editor-metadata) | Export structural param facts (`container` + `arm`) in the editor metadata | medium | done |
| [R-29](#r-29-export-example-tags--curated-example-tiers-in-the-editor-metadata) | Export example tags + curated example tiers in the editor metadata | medium | done |
| [R-30](#r-30-grow-the-curated-example-corpus-recipes--worked-examples) | Grow the curated example corpus (recipes + worked examples) | low | done |
| [R-31](#r-31-normalize-exports-to-one-flat-example-corpus-name-references) | Normalize exports to one flat example corpus (name references) | medium | done |

---

## Theme A — Error model & validation

### R-01. `and`/`or` operators are bitwise, not logical

**Status**: done (option 1) · **Severity**: high · **Spec**: §12.1

`and`/`or`/`&&`/`||` map to `operator.and_`/`or_` — Python’s **bitwise** `&`/`|`.
Correct on `bool` inputs; on ints it computes bit arithmetic (`6 and 3` → `2`); on
most other types it raises a raw `TypeError`. `not` (`operator.not_`) is fine.

**Impact if not fixed**: any template combining non-boolean truthy values (a very
common JSON pattern: “field present and non-empty”) silently computes the wrong
result or crashes with an opaque error. This is the most likely source of silent
data corruption in real pipelines.

**Options**:

1. **(Recommended)** Change `and`/`or` to logical semantics (`lambda a, b: a and b`,
   `a or b`), keeping Python truthiness. Matches JsonLogic and every template
   author’s intuition. *Breaking* for templates that rely on bit arithmetic —
   judged unlikely; needs a changelog entry and a minor version bump.
2. Keep `and`/`or` logical *and* add separate `bitand`/`bitor` operators for anyone
   who needs the old behavior (superset of option 1; near-zero extra cost).
3. Keep current behavior, document loudly, add new `all`/`any` style operators with
   logical semantics. Preserves compatibility but permanently traps newcomers.

**Shipped**: option 1 — `and`/`or`/`&&`/`||` now use logical conjunction/disjunction
with Python truthiness; changelog entry added.

### R-02. Raw Python exceptions escape the error model

**Status**: done (option 1) · **Severity**: high · **Spec**: §12.6, §12.7 + audit

The contract is: `DefinitionError` = bad template, `TransformationError` = bad data.
In practice many code paths leak raw Python exceptions (all verified):

- `attr` only catches `KeyError`/`IndexError`; string-indexing a string or indexing
  a list with a non-int (including `NO_CONTENT`, see ~~R-09~~) raises raw `TypeError`.
- `zip` over non-iterables → raw `TypeError` (`'int' object is not iterable`).
- `expr` with `values: []` → raw `TypeError` from `reduce()` of empty iterable.
- `call` with `values` that isn’t a list → raw `TypeError` from `fn(*values)`.
- `format` with a pattern referencing missing keys/indices → raw `KeyError`/`IndexError`.
- Iteration accessors (`item`, `key`, …) outside `map`/`filter` → raw `KeyError`.
- `expr` operators on incompatible types → raw `TypeError`.

**Impact if not fixed**: callers cannot write a sound `except (DefinitionError,
TransformationError)` boundary — any user-supplied template can crash the host
application with an arbitrary exception. For a library whose templates often come
from config or end users, this is an API-contract hole.

**Options**:

1. **(Recommended)** Wrap each known leak site and re-raise as the appropriate
   transon error with a descriptive message (`TransformationError` for data-shape
   problems, `DefinitionError` for structurally bad parameters like a non-list
   `values`). Exception *type* changes are technically breaking but only convert
   crashes into the documented contract.
2. Additionally add a catch-all in `walk_rule` that wraps any non-transon exception
   into `TransformationError` (with the original chained via `raise … from`).
   Guarantees the contract holds even for unaudited/extension rules, at the cost of
   sometimes masking genuine bugs in rule implementations.
3. Do nothing; document each raw-exception path. Cheapest, but the contract stays
   broken and the docs grow a wall of caveats.

Option 1 and 2 compose; 1 alone already covers all known sites.

**Decision (2026-06-13)**: option 1 — wrap each known leak site; re-raise as
`DefinitionError` or `TransformationError` with a descriptive message.

**Shipped**: option 1 — known leak sites (`attr`, `zip`, `expr`, `call`, `format`,
iteration accessors, `parent`) now raise transon errors; changelog entry added.

### R-03. Reserved-name guard is an `assert` — vanishes under `-O`

**Status**: done (2026-06-13 — explicit checks raising `DefinitionError`, always
active regardless of `-O`; changelog entry added) · **Severity**: high ·
**Spec**: §12.7 + audit

`Context.__contains__/__getitem__/__setitem__` enforce that `this`, `item`, `key`,
`value`, `index` aren’t used as variable names — via `assert`. Verified: under
`python -O` the guard disappears entirely and `{"$": "set", "name": "this"}`
silently writes into the engine’s own context slots, corrupting iteration state.

**Impact if not fixed**: in optimized deployments (`-O`, `PYTHONOPTIMIZE`) templates
can silently shadow engine internals — worst-case silent wrong output. Even without
`-O`, `AssertionError` is the wrong exception type for a user mistake.

**Fix (single obvious option)**: replace asserts with explicit checks raising
`DefinitionError` (it is a template-authoring mistake). Strictly a bugfix; the only
visible change is `AssertionError` → `DefinitionError`.

**Shipped**: explicit `DefinitionError` checks (always active, including under `-O`);
changelog entry added.

### R-04. No template validation; typos and ambiguity pass silently

**Status**: done (option 1) · **Severity**: high · **Spec**: §3.4 + audit

Errors surface only when a branch is walked; dead branches with typos pass forever.
Two adjacent silent-failure modes confirmed by the audit:

- **Unknown parameters are ignored** — `{"$": "attr", "nmae": "x"}` doesn’t error
  on the typo; it errors (or silently misbehaves) for the wrong reason.
- **“Mutually exclusive” parameters are resolved by hidden precedence** — `attr`
  with both `name` and `names` silently uses `name`; `map` with `item`+`key`+`value`
  silently uses `item`; `expr`/`call` with `value`+`values` use `value`. The docs
  say “mutually exclusive” but the engine never enforces it.

**Impact if not fixed**: template bugs ship to production and manifest as wrong
output, not errors — the most expensive failure mode. Hidden precedence also means
the documented contract and real behavior disagree.

**Options**:

1. **(Recommended)** Add an opt-in `Transformer.validate()` (and/or
   `Transformer(template, validate=True)`) that walks the template statically:
   unknown rule names, missing required params, unknown params, ambiguous
   mutually-exclusive combinations → `DefinitionError` up front. Requires rules to
   declare their parameter schema — `register_rule` already collects parameter
   names/docs, so most metadata exists; add “required/exclusive-group” flags.
   Non-breaking (opt-in), big payoff for template-driven products.
2. Enforce mutual exclusivity at walk time only (raise `DefinitionError` when both
   params present). Much smaller; *breaking* for templates that today carry a
   redundant ignored param. Doesn’t catch dead-branch typos.
3. Both: walk-time enforcement now, static `validate()` later. Reasonable sequencing.

**Decision (2026-06-13)**: option 1 — opt-in `validate()` / `validate=True` with
`_required` and `_modes` schema on `register_rule`.

**Shipped**: option 1 — `Transformer.validate()` and `validate=True`; rule schemas on
all built-in rules; changelog and spec §3.4 updated.

### R-05. Error messages carry no template location

**Status**: done (option 1) · **Severity**: medium · **Source**: audit

When a transformation fails deep inside a nested template, the error says *what*
went wrong but not *where* — there is no path like
`template → funcs[1] → map.item → attr` in the message.

**Impact if not fixed**: debugging non-trivial templates degrades to bisection by
hand. Pain grows with template size — exactly where the engine is most useful.

**Options**:

1. **(Recommended)** Thread a lightweight path (list of segments pushed in
   `walk_list`/`walk_dict`/`walk_rule`) and include it when raising/wrapping transon
   errors. Pairs naturally with R-02 option 2 (the wrap point is where you attach
   the path). Minor walk overhead.
2. Exception-annotation-only: catch at `transform()`, attach the path collected via
   a context variable. Less plumbing but easy to get subtly wrong.
3. Do nothing (acceptable while templates stay small; contradicts the library’s
   pitch for complex transformations).

**Decision (2026-06-13)**: option 1 — thread a lightweight path through
`walk_list`/`walk_dict`/`walk_rule` and include it in transon error messages.

**Shipped**: option 1 — `DefinitionError`/`TransformationError` messages append
`at template → …` with dict keys, list indices, rule names, and parameter names;
changelog entry added.

---

## Theme B — `NO_CONTENT` semantics

### R-06. `NO_CONTENT` leaks to the caller at top level

**Status**: done (option 2) · **Severity**: high · **Spec**: §12.2

`transform()` can return the raw `NoContent` sentinel. It is not JSON-serializable;
`json.dumps` crashes, comparisons behave by identity, and the object’s repr leaks
into downstream systems.

**Impact if not fixed**: every consumer must know about (and import) a private-ish
sentinel to handle the “whole template produced nothing” case; most discover it via
a production `TypeError` in `json.dumps`.

**Options**:

1. **(Recommended)** Map top-level `NO_CONTENT` to `None` in `transform()` — same
   normalization the test harness already applies, so the corpus documents this
   meaning anyway. *Breaking* only for callers that explicitly compare against
   `Transformer.NO_CONTENT` (rare; the sentinel was never documented as a public
   return value).
2. Add `transform(data, no_content=None)` so callers choose the substitute
   (`None`, a marker string, raising). Most flexible, slightly wider API.
3. Raise a dedicated exception when the result is `NO_CONTENT`. Makes “produced
   nothing” un-representable as a value — probably too aggressive, `file`-only
   templates legitimately end with `NO_CONTENT`.

**Decision (2026-06-13)**: option 2 — `transform(data, no_content=None)`; callers choose
the substitute (`None` by default, a marker string, or pass `Transformer.NO_CONTENT` to
receive the raw sentinel).

**Shipped**: option 2 — `transform(data, no_content=None)`; default maps to `None`;
changelog entry added.

### R-07. `NO_CONTENT` leaks into `format` output

**Status**: done (option 1) · **Severity**: high · **Spec**: §12.3

`format` interpolates the sentinel’s repr:
`"<transon.transformers.NoContent object at 0x…>"` ends up in output strings
whenever a formatted value is missing (verified, including via list/dict unpack).

**Impact if not fixed**: garbage strings silently flow into output documents —
a silent-corruption bug, worse than a crash because nothing fails.

**Options**:

1. **(Recommended)** `format` returns `NO_CONTENT` when the value (or any unpacked
   element/entry) is `NO_CONTENT` — consistent with `map`/`object` skip semantics,
   composes with `map` skipping and R-10 defaults.
2. Raise `TransformationError` on missing values. Louder, but makes
   missing-data-tolerant templates harder to write.
3. Substitute `""` for missing values. Convenient but lossy — can’t distinguish
   “missing” from “empty” downstream; not recommended.

**Decision (2026-06-13)**: option 1 — `format` returns `NO_CONTENT` when the value (or any
unpacked list element or dict key/value) is `NO_CONTENT`.

**Shipped**: option 1 — `format` propagates `NO_CONTENT`; optional `default` param;
changelog entry added.

### R-08. `join` is inconsistent with `NO_CONTENT` items

**Status**: done (option 1) · **Severity**: medium · **Spec**: §12.4

A `NO_CONTENT` item in `join.items` falls through all type checks and raises
`TransformationError: Can't join items` — unlike `map`/`object`/`file`/`filter`,
which skip.

**Impact if not fixed**: the natural pattern “join whichever of these optional
fields exist” crashes instead of degrading gracefully; authors work around it with
a redundant `filter`/`map` pass.

**Options**:

1. **(Recommended)** Filter `NO_CONTENT` items out before type dispatch — aligns
   `join` with the documented skip semantics. Edge effect: combines with ~~R-12~~
   (done) (all-items-missing → empty-list case; now returns `NO_CONTENT`).
2. Keep raising, but with a precise message (“item 2 is NO_CONTENT”). Honest but
   keeps `join` the odd one out.

**Decision (2026-06-13)**: option 1 — filter `NO_CONTENT` items out before type dispatch.

**Shipped**: option 1 — `join` skips `NO_CONTENT` items; changelog entry added.

### R-09. `NO_CONTENT` as a dynamic name (`attr`/`set`/`get`)

**Status**: done (option 1) · **Severity**: medium · **Source**: audit

When a dynamic `name` itself evaluates to `NO_CONTENT` (e.g. `{"$": "get"}` of an
undefined variable feeding `attr`):

- `attr` on a **dict**: `KeyError` → `NO_CONTENT` (fine, accidentally).
- `attr` on a **list**: raw `TypeError: list indices must be integers …, not NoContent`.
- `set`/`get`: silently store/retrieve a variable keyed by the sentinel object —
  it “works” but is meaningless and masks the upstream miss.

**Impact if not fixed**: behavior depends on the *data type being indexed*, which
template authors can’t always control; the `set` case hides bugs.

**Options**:

1. **(Recommended)** Treat a `NO_CONTENT` name uniformly: `attr` returns
   `NO_CONTENT` (missing path → missing value, matching sentinel absorption);
   `set`/`get` raise `TransformationError` (assigning to a missing name is a logic
   error, not a missing value).
2. Raise `TransformationError` in all three rules. Stricter; makes “optional deep
   lookup via computed key” patterns crash.

**Decision (2026-06-13)**: option 1 — `attr` returns `NO_CONTENT` when the dynamic
name (or any path segment) is `NO_CONTENT`; `set`/`get` raise `TransformationError`.

**Shipped**: option 1 — uniform `attr` absorption; `set`/`get` error on
`NO_CONTENT` names; changelog entry added.

### R-10. No default-value mechanism

**Status**: done (option 1) · **Severity**: medium · **Source**: audit (feature gap)

There is no way to say “this value, or X if missing”. Every `NO_CONTENT` consumer
problem (R-06/07/08) is partially a symptom: authors have no tool to stop sentinel
propagation at the point of lookup.

**Impact if not fixed**: missing-data handling needs verbose workarounds (or is
impossible — there is no conditional rule to branch on “missing”), so templates
over real-world sparse JSON get brittle.

**Options**:

1. **(Recommended)** Add an optional `default` parameter (dynamic) to the producers:
   `attr`, `get`, and optionally `format`/`include`. Returned instead of
   `NO_CONTENT`. Backward compatible, local, self-documenting.
2. A standalone `default` rule (`{"$": "default", "value": …}`) that replaces
   `NO_CONTENT` in `this` — composes with `chain` everywhere, one new rule instead
   of N parameters. Slightly more verbose at use sites.
3. Both (parameter for the common case, rule for composition). Defensible since
   both are small.

**Decision (2026-06-13)**: option 1 — optional dynamic `default` parameter on `attr`, `get`,
`format`, and `include`; returned instead of `NO_CONTENT` when the lookup/format/include
would otherwise produce no value.

**Shipped**: option 1 — `default` on `attr`, `get`, `format`, `include`; changelog
entry added.

---

## Theme C — JSON purity & data integrity

### R-11. `zip` emits Python tuples and inherits Python `zip` quirks

**Status**: done (option 2) · **Severity**: medium · **Spec**: §12.8 + audit

`rule_zip` returned `list(zip(*items))` → a list of **tuples**. Tuples serialize via
`json.dumps` but are not lists: `join` of zipped rows raised `TransformationError`
(verified), strict equality/round-trip checks failed. Also inherited from Python
`zip`: strings are zipped character-wise, and non-iterable items raised raw
`TypeError` (→ ~~R-02~~).

**Impact if not fixed**: violates the core promise “output is JSON”; `zip` results
are second-class values inside the engine itself.

**Options**:

1. **(Recommended)** Return lists of lists (`[list(row) for row in zip(*items)]`),
   raise `TransformationError` unless every item is a list. *Breaking* only for
   callers inspecting Python types of the output (tuples were never representable
   in JSON anyway) and for anyone deliberately zipping strings.
2. Lists of lists, but keep accepting any iterable (strings zip char-wise).
   Preserves a behavior that is almost certainly never intentional in JSON land.

**Shipped**: option 2 — each output row is a list; any iterable item is accepted;
non-iterables raise `TransformationError`.

### R-12. `join` of an empty list returns `""`

**Status**: done (option 1 refined + falsy sentinel) · **Severity**: low · **Spec**: §12.5

`all()` over an empty list is vacuously true, so the all-strings branch wins:
joining zero dicts yields `""` instead of `{}`.

**Impact if not fixed**: a `map`+`join` pipeline that merges dicts changes *output
type* when the input collection is empty — a classic edge-case production bug.

**Options**:

1. **(Recommended)** Make empty-input behavior explicit via an optional constant
   parameter, e.g. `"empty": "dict" | "list" | "string"` (default `"string"` keeps
   compatibility). Authors who hit the bug get a one-word fix.
2. Infer intent from the *template* (impossible — items are dynamic) or always
   return `NO_CONTENT` for empty input (breaking, and surprising in string
   pipelines). Not recommended.

**Decision (2026-06-13)**: option 1 refined — `join` returns `NO_CONTENT` when there are
no items to join (including when all items are `NO_CONTENT`); optional dynamic `default`
parameter supplies a fallback value (same pattern as `attr`/`get`/`format`/`include`).
Additionally, `NoContent` is falsy so `expr` `or`/`and` can compose fallbacks in `chain`
(e.g. `join` → `expr` `or` `{}`).

**Shipped**: option 1 refined + falsy sentinel — empty `join` returns `NO_CONTENT` with
optional `default`; `NoContent.__bool__` is `False`; changelog entry added.

### R-13. Output aliases input data (shared mutable structures)

**Status**: done · **Severity**: medium · **Source**: audit

`transform()` never mutates input — but rules like `this`/`attr`/`item` return
*references* into the input. Verified: mutating the output afterwards mutates the
original input object.

**Impact if not fixed**: callers who post-process the output corrupt their own
input (cache poisoning, double-transform bugs). The invariant “transform never
mutates input” is true only until the caller touches the result.

**Options**:

1. Deep-copy values at the rule boundaries that pass input references through.
   Safe but a real performance cost on large documents.
2. **(Recommended)** Document the aliasing prominently (spec + `transform()`
   docstring) and add an opt-in `transform(data, copy_output=True)` (or constructor
   flag) that deep-copies the final result once. One copy at the end is cheaper
   than per-rule copies and only paid by callers who need it.
3. Do nothing. The trap stays invisible until it fires.

**Decision (2026-06-13)**: option 2 — keep the default behavior (output may alias the
input; one copy of input data is never made for the common case) and add an opt-in
`transform(data, copy_output=True)` keyword that deep-copies the final result exactly
once before returning. The aliasing is documented prominently in the spec (§3.1, §10)
and the `transform()` docstring so callers who post-process the result know to opt in.

**Shipped**: option 2 — `transform(data, no_content=None, *, copy_output=False)`. When
`copy_output=True`, the returned value is `copy.deepcopy`-ed once at the `transform()`
boundary so it shares no mutable structure with the input. Default (`False`) is
unchanged: rules like `this`/`attr`/`item` still return references into the input, and
this aliasing is now documented. Stdlib only (`copy`); no input/template mutation.

### R-14. No escape for a literal marker (`$`) key

**Status**: done (option 4) · **Severity**: medium · **Spec**: §12.9

Data containing `"$"` as a plain key cannot be written literally in a template —
any dict with the marker key is dispatched as a rule. Workarounds: the `object`
rule (one pair at a time) or changing the marker (template-wide, breaks sharing).

**Impact if not fixed**: a whole class of documents (MongoDB queries/aggregations,
JSON-RPC-ish payloads, currency fields) can’t be produced naturally; transon can’t
transform templates *about* transon.

**Options**:

1. **(Recommended)** A `quote`/`literal` rule: `{"$": "quote", "value": {…}}`
   returns its `value` verbatim without walking. Purely additive, solves nesting of
   arbitrary literal structures, mirrors Lisp quoting; an optional companion
   `unquote` could be added later if templating inside quoted blocks is ever needed.
2. Marker-escaping convention, e.g. key `"$$"` in a literal dict is emitted as
   `"$"`. Handles the key-name case (even deep inside literal data) but adds a
   rewrite pass over all literal dicts and a new reserved spelling — and `"$$"`
   itself then needs escaping.
3. Both — quoting for blocks, escaping for single keys. Decide if option 1 alone
   proves insufficient.

**Decision (2026-06-13)**: option 4 (refinement of the rejected new-rule idea) —
**extend the existing `object` rule** with a `fields` mode instead of adding a new
keyword. `{"$": "object", "fields": {…}}` takes a literal mapping: keys are emitted
verbatim (including the marker `$`), values are walked as templates. This is purely
additive, introduces no new rule name (no change to the registry/`get_rules` set),
preserves partial templating (every value is dynamic), and only upgrades the existing
"workaround is the `object` rule" note in the spec. The all-static-deep-block case
(a future `quote` rule) is deferred as still-rare. Companion key-escaping (option 2)
is not pursued.

**Shipped**: option 4 — `object` rule extended with a `fields` mode
(`{"$": "object", "fields": {…}}`): literal keys (including the marker `$`), dynamic
values, `NO_CONTENT` values omitted. No new rule keyword; `validate()` recurses into
`fields` values; changelog entry added.

---

## Theme D — Language design & consistency

### R-15. `set` scoping is subtle and undocumented

**Status**: done (option 1) · **Severity**: medium · **Spec**: §2.2, §4.2

Whether a variable set by `set` is visible to a sibling template depends on the
exact context object the `set` executed in: directly at a literal-dict key or as
the *first* `chain` func → visible to later siblings; inside a later `chain` step
or a `map` item → invisible. This falls out of `derive()` copy semantics plus
which rules derive scopes, and is documented only in the spec for engine
developers, not for template authors.

**Impact if not fixed**: templates relying on sibling visibility also silently
depend on dict key order and on `chain` position; refactoring a working template
(wrapping a step in `chain`, reordering keys) changes variable visibility with no
error.

**Options**:

1. **(Recommended)** Specify the current behavior precisely as *the* scoping rule
   and document it for template authors (rule docs for `set`/`get` + a docs-site
   section with examples). Zero breakage; turns a quirk into a contract.
2. Make scoping strictly lexical: every composite rule derives a child scope, and a
   `set` is never visible outside the sub-template it occurs in; introduce an
   explicit export mechanism if cross-step variables are needed. Cleaner model but
   *breaking* for the documented first-chain-func pattern, and needs new machinery.
3. Make `set` deliberately context-transparent (visible to all later evaluation in
   the same `transform()` call) — simplest mental model (“template-global
   variables”), but legalizes evaluation-order coupling everywhere.

**Decision (2026-06-13)**: option 1 — document current scoping as the contract.

**Shipped**: option 1 — spec §2.2 scoping table, `set`/`get` rule docs, and seven
example cases in `transon/tests/test_set.py`; behavior unchanged.

### R-16. Constant vs dynamic parameters are inconsistent

**Status**: done (option 2) · **Severity**: low · **Source**: audit

Most rule parameters are templates (walked); a handful are read verbatim:
`expr.op`, `call.name`, and `chain.funcs` list structure. Previously `join.sep`
and `format.pattern` were also constant, which caused raw Python errors when
authors passed templates in those slots.

**Impact if not fixed**: authors must memorize per-parameter rules; mistakes
surface as raw Python errors rather than evaluated templates or clear errors.

**Options**:

1. Document constness per parameter (audit all `register_rule`
   param docs), and raise `DefinitionError` when a constant parameter receives a
   dict containing the marker. Keeps semantics, fixes diagnostics.
2. Make conservative parameters dynamic where harmless (`join.sep`,
   `format.pattern` could be walked). More uniform, but dynamic `expr.op` /
   `call.name` would make static validation impossible — at minimum keep
   those constant (~~R-04~~, done).

**Decision (2026-06-13)**: option 2 — walk `join.sep` and `format.pattern`; keep
`expr.op`, `call.name`, and `chain.funcs` list structure constant.

**Shipped**: option 2 — `join.sep` and `format.pattern` are walked; non-string
results raise `TransformationError`; param docs and spec updated; changelog entry
added.

### R-17. `include` has no cycle/depth protection; default loader raises `RuntimeError`

**Status**: done (option 1 with name tracking) · **Severity**: low · **Source**: audit

A `template_loader` that permits cycles (e.g. `docs.template_loader` includes any
test case by name) lets two templates include each other → raw `RecursionError`.
Separately, using `include` without configuring a loader raises `RuntimeError`,
outside the transon error model (another R-02 instance).

**Impact if not fixed**: stack-overflow crash with a useless traceback in template
ecosystems with shared/included templates; inconsistent error type for a common
misconfiguration.

**Options**:

1. **(Recommended)** Change the default loader to raise `DefinitionError`; add a
   simple include-depth counter (e.g. limit 50, overridable) raising
   `TransformationError` with the include chain in the message.
2. Track the actual chain of include names and detect true cycles (precise, a bit
   more state threading through nested transformers). Depth limit is simpler and
   catches the same accidents.

**Decision (2026-06-13)**: option 1 with name tracking — `DefinitionError` from the
default loader; depth limit (default 50, overridable) with include name chain in
`TransformationError` messages.

**Shipped**: option 1 with name tracking — default loader raises `DefinitionError`;
`max_include_depth` on `Transformer` (default 50); depth exceeded raises
`TransformationError` with name chain; changelog entry added.

### R-18. `include` rule has no docstring

**Status**: done · **Severity**: low · **Spec**: §12.11

The only rule whose generated documentation is `doc: null`. Fix: write the
markdown docstring on `rule_include` covering loader delegation, the
value-only boundary (no variable/context crossing), and `NO_CONTENT` propagation.
Impact of not fixing: a documented feature is invisible on the docs site/playground.

**Shipped**: added `rule_include` docstring (loader delegation, value-only boundary,
`NO_CONTENT` propagation); tagged existing corpus example with `include:name`.

### R-19. Docs: `expr` with `values` ignores `this` — underemphasized

**Status**: done · **Severity**: low · **Spec**: §12.10

Intended behavior, stated once in prose. Easy to misuse since every other mode
involves `this`. Fix: add a warning callout in the `values` parameter doc and a
corpus example demonstrating the ignored-context behavior. No code change.

**Shipped**: warning callout on `expr` `values` parameter doc; corpus example
`ExprValuesIgnoresThis` (`1+2+3` with unrelated input string).

---

## Theme E — Infrastructure & code quality

### R-20. Python version policy: 3.7 is EOL, no 3.12/3.13 in CI

**Status**: done (option 1) · **Severity**: medium · **Source**: audit

CI runs 3.7–3.11. Python 3.7 reached end-of-life in June 2023; meanwhile 3.12/3.13
are untested (risk: stdlib deprecations/removals break the engine unnoticed).

**Impact if not fixed**: the project pays an ongoing tax (forbidden-syntax rules,
`importlib-metadata` backport, old CI images that will eventually disappear) to
support an interpreter nobody should run, while offering no guarantee on the
interpreters people actually use.

**Options**:

1. **(Recommended)** Add 3.12/3.13 to the CI matrix now (no code change expected);
   in the next minor release bump `python_requires` to ≥3.8 (or ≥3.9), drop the
   `importlib-metadata` backport, and retire the 3.7 compat rules.
2. Add 3.12/3.13 to CI but keep 3.7 support indefinitely. Zero breakage; keeps the
   compat tax forever.
3. Jump straight to ≥3.9 or ≥3.10. More cleanup headroom; drops users on old
   distro Pythons — decide based on actual user base.

**Decision (2026-06-13)**: option 1 — CI 3.9–3.13; `requires-python >=3.9`; drop
`importlib-metadata` backport; retire 3.7 compat rules; migrate Poetry → uv.

**Shipped**: option 1 — `requires-python >=3.9`, uv packaging, CI matrix 3.9–3.13;
changelog entry added.

### R-21. Broken type annotations in `transformers.py`

**Status**: done · **Severity**: low · **Source**: audit

`FileWriterType = Callable[[str, any], NoReturn]` uses the builtin function `any`
instead of `typing.Any`, and `NoReturn` (function never returns) instead of `None`
(returns nothing). Harmless at runtime, wrong under any type checker.
Fix: `Callable[[str, Any], None]`. Impact of not fixing: type checkers report
nonsense for anyone integrating the library; signals low typing hygiene.

**Shipped**: `FileWriterType` corrected to `Callable[[str, Any], None]`.

### R-22. `Context.derive` copies all variables on every scope

**Status**: done (option 1, copy-on-write) · **Severity**: low · **Source**: audit

`derive()` copies the entire variable dict into every child context (every `map`
iteration, every `chain` step). With V variables and N iterations that is O(V×N)
copying, although the linked `parent` chain already exists and could serve lookups.

**Impact if not fixed**: quadratic-ish overhead for variable-heavy templates over
large collections. Irrelevant for small documents — measure before optimizing.

**Options**:

1. Lookup-through-parent-chain (`get`/`__contains__` walk `parent` links; `derive`
   stores only the new props). Caution: this *changes* R-15 scoping observable
   behavior (a `set` in a parent after derivation would become visible to an
   already-derived child only under copy semantics — actually the reverse: chain
   lookup sees later parent sets, copying does not). **Must be decided together
   with R-15.**
2. Keep copying; revisit only if profiling shows it matters. **(Recommended for
   now)** — correctness items above are worth more than this optimization.

**Decision (2026-06-13)**: option 1 with copy-on-write — `derive()` stores only
new props; reads walk the parent chain; the first `set` in a derived scope
materializes a snapshot of inherited variables so writes stay isolated. Preserves
R-15 scoping in practice (sequential evaluation never mutates a parent mid-child);
avoids O(V) copying on read-only `map`/`chain` steps.

**Shipped**: option 1 with copy-on-write — `derive()` stores only new props; reads and
iteration-slot accessors walk the parent chain; first `set` materializes inherited
variables for write isolation.

---

## Theme F — Editor metadata & projection support

> These items are the engine-side dependencies of the `transon-blockly` *template-driven editor*
> pivot. They are **additive** (no change to existing template semantics) and are specified from the
> consumer side in `transon-blockly/docs/metadata-contract.md` §6 and detailed in
> [`proposals/editor-metadata-export.md`](proposals/editor-metadata-export.md). Decisions were
> ratified as that repo's open questions OQ-012…OQ-015 (2026-06-27).

### R-23. `switch` and `cond` lazy-dispatch rules

**Status**: done (cross-repo decision OQ-012) · **Severity**: medium · **Source**: transon-blockly metadata-contract §6.1

Two lazy multi-way dispatch rules where **only the selected branch is evaluated**: `switch`
(equality on a key, cases as a JSON object, optional `default`) and `cond` (Lisp-style ordered
`[{when, then}, …]` + optional `default`, subsuming `if`). The editor's generated codec dispatches
on rule name / block type with these, and derives input widgets from `kind` + `options`.

**Impact if not fixed**: the editor's compiler model cannot run — its projections need lazy dispatch
to avoid evaluating every arm, and there is no in-engine substitute that preserves `NO_CONTENT`
discipline.

**Requirements**: only the chosen branch is walked; honor `NO_CONTENT`; `DefinitionError` for a
malformed template (e.g. a `cond` arm missing `when`/`then`), `TransformationError` for bad data;
stdlib-only, Python 3.9+, no input/template mutation; ordinary JSON rules (no new transformation
language). SPEC-first: add the rule text to `SPECIFICATION.md`, then table-driven example cases in
`transon/tests/`.

**Shipped (v0.1.1)**: `rule_switch` / `rule_cond` in `transon/rules.py` (lazy; only the selected
branch is walked; `NO_CONTENT`/`default` honored); documented in `SPECIFICATION.md` (rules table);
example corpus `transon/tests/test_switch.py` + `test_cond.py`; error paths `tests/test_switch_cond.py`.

### R-24. `get_editor_metadata()` projection-ready export

**Status**: done (cross-repo decision OQ-015) · **Severity**: medium · **Source**: transon-blockly metadata-contract §2, §3, §6.2

A dedicated, versioned editor-metadata export (separate from the docs API) emitting the contract's §2
shape: **pre-derived variant signatures** (computed in Python from `required`/`modes`), per-param
**`kind`** (`dynamic`/`constant`), **resolved enum domains** (`options`) for closed constants
(`expr.op`, `call.name`), operator/function metadata, a **split** structural-catalog vs examples/docs
payload, and a standalone `metadata_version`. Greenfield at v0.1.0.

**Impact if not fixed**: the editor has no single source for its palette/toolbox/codec projections
and would be forced to hand-maintain a parallel catalog — exactly what the pivot removes.

**Requirements**: emit **engine facts only** — no Blockly shapes, colours, or widget choices (the
editor stays the only place that knows Blockly). The editor runs engine-parity checks against this
export, so drift is caught in CI on the editor side.

**Shipped (v0.1.1)**: `transon/metadata.py::get_editor_metadata()` — split `catalog`/`docs` payload,
pre-derived `variants` (`derive_variants`), per-param `kind` (`dynamic`/`constant`), resolved
`options` for `expr.op`/`call.name`, standalone `metadata_version` + `engine_version`; tests
`tests/test_metadata.py`; consumed as `from transon.metadata import get_editor_metadata` (mirroring
`transon.docs.get_all_docs`, not re-exported from the package root). **Editor-side integration
(resolved 2026-06-27):** `title`/`category`/`advanced`
are intentionally **not** emitted — presentation is editor-owned (`transon-blockly`
metadata-contract §2.1/§2.7/§2.8) and the engine stays presentation-agnostic. The editor's
engine-parity check reads the split `catalog` shape; `switch`/`cond` are first-class authored rules
(editor SPEC §14.16) checked like any other rule.

### R-25. `include` default-marker inheritance

**Status**: done (cross-repo decision OQ-014) · **Severity**: low · **Source**: transon-blockly metadata-contract §6.3

When an `include`d template does not pin its own marker, it inherits the **parent's default marker**
instead of always assuming `"$"`, so the editor's staged generator templates (the `@`/`$` compile
phases) stay consistent across `include` boundaries.

**Impact if not fixed**: staged generator-splitting breaks at `include` boundaries; the editor would
need a workaround that the contract explicitly declines.

**Requirements**: **no** free per-call `marker` argument on `include`; **no** `eval`/`apply` added
to the engine; `quote`/`raw` declined. SPEC-first: update `SPECIFICATION.md` and the `include`
docstring, and add a focused inheritance test. Relates to ~~R-14~~ (done) (literal-marker handling).

**Shipped (v0.1.1)**: `transon/rules.py::rule_include` inherits the parent transformer's marker only
when the sub-template still uses the default `$` (a pinned non-default marker is kept; no per-call
`marker` argument); documented in `SPECIFICATION.md` (`include` row); test `tests/test_include_marker.py`.

### R-26. `type` value-type function

**Status**: done · **Severity**: medium · **Source**: [`proposals/type-function.md`](proposals/type-function.md) (Deliverable 1)

A **total**, non-throwing `call` function returning a value's JSON type name
(`object`/`array`/`string`/`int`/`float`/`boolean`/`null`). It is the one operation a `switch`/`cond`
key can safely apply to a node of unknown type, so the `transon-blockly` editor's generated codec
collapses its per-node type dispatch to a single `switch` keyed on `type` instead of the verbose
two-step `expr == [this, str(this)]` + first-char idiom.

**Impact if not fixed**: every dispatch point in every projection template repeats the brittle two-step
type probe; there is no total in-engine way to ask "what type is this value?".

**Requirements**: total over every JSON value (never throws on well-formed data); pure, stdlib-only,
Python 3.9+, no input mutation; flows through `get_editor_metadata()` (so `call.name` gains `type`)
and `get_functions()` docs; ordinary function — no new transformation language. SPEC-first: add the
function to `SPECIFICATION.md` §4.8 and `call.name` docs, then table-driven example cases.

**Shipped**: `_json_type` registered as `type` in `transon/functions.py` (tokens
`object|array|string|int|float|boolean|null`); documented in `SPECIFICATION.md` (§4.8 + `call.name`
table) and `rules.py` `call.name` param; example corpus `transon/tests/test_type.py`; metadata
parity updated in `tests/test_metadata.py`.

### R-27. `include` propagates `template_loader` through context

**Status**: done · **Severity**: medium · **Source**: [`proposals/type-function.md`](proposals/type-function.md) (Deliverable 2)

A recursive/self-`include`ing codec skeleton needs the sub-`Transformer` built by `include` to inherit
the parent's `template_loader` (it already inherited the include-stack/marker/depth). Rather than adding
another in-place mutation of the loaded instance — unsafe when a loader returns a cached/shared
`Transformer` — the inherited include-context is **passed through the loader** so the sub-transformer is
constructed correctly.

**Impact if not fixed**: self-referential codecs fail to re-resolve ("include not resolvable") unless
every host re-patches the loader on each resolved include (the editor's Node adapter and the production
Pyodide host would each need the identical workaround).

**Requirements**: do not mutate the loaded instance; `include` always calls the `template_loader` as
`loader(name, context=...)`, handing it an `IncludeContext` from which it constructs the
sub-`Transformer` with the inherited loader/marker/depth/stack; `context` is optional in the loader
signature so a loader may also be invoked standalone; additive, no template-semantics change.
SPEC-first: update the `include` row + constructor parameters in `SPECIFICATION.md`.

**Shipped**: `IncludeContext` in `transon/transformers.py` (and a new `include_stack` constructor
parameter); `rule_include` always passes the context and the loader constructs the sub-`Transformer`
(e.g. `context.transformer(template)`); the engine never mutates the loaded instance; documented in
`SPECIFICATION.md` (`include` row + constructor) and the `rule_include` docstring; tests
`tests/test_include_loader_context.py`.

### R-28. Export structural param facts (`container` + `arm`) in the editor metadata

**Status**: done (cross-repo decision 2026-07-02, `transon-blockly` UAT #1/#2 brainstorm —
engine-first shape hints; editor-side shape catalog rejected) · **Severity**: medium ·
**Source**: [`proposals/editor-metadata-structural-params.md`](proposals/editor-metadata-structural-params.md)

`get_editor_metadata()` (R-24) drops two structural facts the engine already declares at the rule
source and enforces in validation/the walk: `ParamSpec.container`
(`template`/`mapping`/`list`/`arms` — `chain.funcs`, `object.fields`, `switch.cases`, `cond.cases`)
and `ParamSpec.arm` (the `ArmSpec` slot schema for `cond.cases`: required `when`/`then` + per-slot
specs). The `transon-blockly` editor needs them to project structured rule parameters as single
coherent blocks (repeating inputs / when-then groups / key-value rows) instead of compositions of
generic array/object blocks.

**Impact if not fixed**: the editor either renders every dynamic param as one generic socket
(structured templates degrade into raw-JSON block assemblies — its UAT findings #1/#2) or
re-declares these facts in a parallel editor-side catalog, exactly the duplication R-24 removed.

**Requirements**: additive only — emit `container` when not `template` (omit for the default) and
`arm: {required, params}` for `ARMS` params (recursive serializer, same shape as rule params;
faithful to `ArmSpec` — no invented `variants` key); optionally arm-slot docstrings in the docs
payload; bump `METADATA_VERSION` `2.0` → `2.1`; **engine facts only** (no widget/presentation
vocabulary, contract §2.8); no change to rules, walker, validation, or template semantics; do NOT
annotate `TEMPLATE` params (`map.items` etc. accept dynamic templates — a single socket is the
honest rendering). Tests extend `tests/test_metadata.py`.

**Shipped**: `_catalog_param` in `transon/metadata.py` serializes each `ParamSpec` recursively —
`container` emitted when not the default `template`, `arm: {required, params}` for `ARMS` params
(arm slots use the same serialization as rule params); the docs payload's `cond.cases` entry gains
an `arms` list with the `when`/`then` slot docstrings; `METADATA_VERSION` `2.0` → `2.1`; no change
to rules, validation, or the walker. Tests in `tests/test_metadata.py` (container/arm export,
no-key-for-`TEMPLATE` sweep, docs arm descriptions, version bump).

### R-29. Export example tags + curated example tiers in the editor metadata

**Status**: done · **Severity**: medium ·
**Source**: [`proposals/editor-metadata-example-tiers.md`](proposals/editor-metadata-example-tiers.md) (Deliverable 1)

The tagged `TableDataBaseCase` corpus is the engine's single example source, and it already holds
two curated tiers (`worked-example`, `recipe`) that `get_all_docs()` exposes as first-class blocks.
But `get_editor_metadata()` exposed neither, and the shared example serializer
(`docs.get_test_cases_for_tag()`) stripped `tags` — the corpus's own organizing metadata. The
editor's Examples surface could only flatten the per-entry reference examples into one long list of
fixture-named cases, and had to dedupe re-inlined multi-tagged cases by content hash.

**Impact if not fixed**: a reference corpus posing as a demo showcase in the editor; consumers
re-derive grouping/dedup facts the engine already owns.

**Requirements**: additive only — emit `tags` on every serialized example (flows into
`get_all_docs()` too; the docs site ignores unknown fields) and add `docs.worked_examples` /
`docs.recipes` blocks to `get_editor_metadata()` mirroring `get_all_docs()`; conventions stated in
docstrings (curated cases carry **only** their tier tag; reference cases never carry a tier tag);
no display order, difficulty, titles, or presentation vocabulary (editor-owned); bump
`METADATA_VERSION` `2.1` → `2.2`. Tests extend `tests/test_metadata.py`.

**Shipped**: `docs.get_test_cases_for_tag()` emits `'tags': list(case.tags)`;
`get_editor_metadata()` docs payload gains `worked_examples` + `recipes` (same serializer);
`METADATA_VERSION` `2.1` → `2.2`; conventions documented in the `get_worked_examples()` /
`get_recipes()` / `get_editor_metadata()` docstrings. Tests in `tests/test_metadata.py` (tags on
entry-, param-, operator-, and function-level examples; tier blocks non-empty and tier-tag-only;
reference examples never tier-tagged; version bump).

### R-30. Grow the curated example corpus (recipes + worked examples)

**Status**: done · **Severity**: low ·
**Source**: [`proposals/editor-metadata-example-tiers.md`](proposals/editor-metadata-example-tiers.md) (Deliverable 2)

The curated tiers predated `switch`/`cond` (R-23) and skipped several rules users reach for early
(`set`/`get`, `zip`, comparison-based `filter`). Content-only change: every rule family a
first-time user meets (`accessors`, `map`/`filter`, `object`, `expr`, `switch`/`cond`, `set`/`get`,
`zip`, `format`/`join`/`call`) must appear in at least one curated case, at the existing docstring
quality bar (task-framed bold title + *"Task: …"* line).

**Shipped**: five recipes — `RecipeMapCodeToLabel` (`switch` + `default`),
`RecipeBucketValueByRanges` (`cond` arms with `expr` comparisons), `RecipeComputeOnceUseTwice`
(`set`/`get` in a `chain`), `RecipePairUpTwoLists` (`zip` + `map`/`object`),
`RecipeKeepItemsMatchingCondition` (`filter` + `expr` comparison) — and one worked example,
`WorkedExampleConditionalEnrichmentInsideMap` (`map` + `object` + `switch` + `cond`), in
`transon/tests/test_recipes.py` / `test_worked_examples.py`. `tests/test_docs.py` name lists
extended plus a rule-family coverage sweep over the curated corpus.

### R-31. Normalize exports to one flat example corpus (name references)

**Status**: done · **Severity**: medium ·
**Source**: [`proposals/example-corpus-normalization.md`](proposals/example-corpus-normalization.md)

Both export APIs re-inlined the full example object under every entry a case's tags attached it
to: 121 corpus cases became 264 inlined objects, ~60 % of each ~135 KB payload was repeated
example bodies, and two untagged cases (`AttrSimplePathDoesNotExist1/2`) appeared in **no** export
at all. The R-29 RFC explicitly deferred the fix ("normalize to one flat tagged corpus") as a
`3.0` candidate.

**Impact if not fixed**: payload duplication grows with every new multi-tagged case; consumers
keep content-hash dedupe workarounds; untagged orphans stay invisible.

**Requirements**: shape-breaking, both APIs — a flat `examples` block (every case serialized
exactly once, `tags` kept) with every other `examples` field (rule/param/operator/function +
curated tiers) an ordered list of `name` references into it; the join stays engine-owned
(consumers resolve names, never re-derive tag conventions); `errors` stays inline (no
duplication there); tag the two orphan cases; bump `METADATA_VERSION` `2.2` → `3.0`; align
`SPECIFICATION.md` §5/§5.1/§6.1; coordinated consumer migrations (docs site + `transon-blockly`
contract §2.7, SPEC-first there).

**Shipped**: `docs.get_example_corpus()` + `serialize_case()` + `get_example_names_for_*` name
helpers replace the inline per-tag serializers; `get_all_docs()` and `get_editor_metadata()`
emit the flat corpus + name references; orphans tagged `attr:names`; `METADATA_VERSION` `2.2` →
`3.0`. Corpus invariants tested in `tests/test_docs.py` / `tests/test_metadata.py`: unique names,
every reference resolves, every case reachable, curated cases tier-tag-only, reference examples
never tier-tagged. `SPECIFICATION.md` §5/§5.1/§6.1 rewritten to the new shapes.

---

## Suggested sequencing

1. **No-decision fixes** (can start immediately): ~~R-03~~ (done), ~~R-18~~ (done), ~~R-19~~ (done), ~~R-21~~ (done).
2. **Error-model batch** (one minor release, loud changelog): ~~R-01~~ (done), ~~R-02~~ (done), ~~R-09~~ (done),
   ~~R-16~~ (done), ~~R-17~~ (done) — all convert crashes/silent wrongness into documented
   errors.
3. **NO_CONTENT batch**: ~~R-06~~ (done), ~~R-07~~ (done), ~~R-08~~ (done), ~~R-10~~ (done) — semantics
   interlock; shipped together.
4. **Feature work**: ~~R-04~~ (done), ~~R-05~~ (done), ~~R-11~~ (done), ~~R-12~~ (done), ~~R-14~~ (done).
5. **Policy/long-term**: ~~R-13~~ (done), ~~R-15~~ (done), ~~R-20~~ (done), ~~R-22~~ (done).
