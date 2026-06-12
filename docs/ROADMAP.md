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
> described behaviors are verified against the implementation (v0.0.7).

**Statuses**: `needs-decision` (maintainer must pick an option) ·
`accepted` (option chosen, ready to implement) · `in-progress` · `done` ·
`rejected` (decided to keep current behavior — record why).

## Policy decisions (recorded 2026-06-13)

1. **Compatibility**: pre-1.0 freedom — behavior-changing fixes may change defaults
   directly, with a changelog entry and a minor version bump. No opt-in flags
   required for compatibility's sake alone. This unblocks the breaking-change
   concern in R-01, R-02, R-06, R-07, R-11 (each still needs its per-item option
   chosen, but "is breaking acceptable" is settled: yes, with changelog).
2. **Python versions**: R-20 option 1 accepted — add 3.12/3.13 to CI now; in the
   next minor release require ≥3.8 (or ≥3.9), drop the `importlib-metadata`
   backport, and retire the 3.7 compat rules.

## Checklist

| ID | Title | Severity | Status |
|---|---|---|---|
| [R-01](#r-01-andor-operators-are-bitwise-not-logical) | `and`/`or` operators are bitwise, not logical | high | needs-decision |
| [R-02](#r-02-raw-python-exceptions-escape-the-error-model) | Raw Python exceptions escape the error model | high | needs-decision |
| [R-03](#r-03-reserved-name-guard-is-an-assert-vanishes-under--o) | Reserved-name guard is an `assert` — vanishes under `-O` | high | accepted |
| [R-04](#r-04-no-template-validation-phase-typos-and-ambiguity-pass-silently) | No template validation; typos and ambiguity pass silently | high | needs-decision |
| [R-05](#r-05-error-messages-carry-no-template-location) | Error messages carry no template location | medium | needs-decision |
| [R-06](#r-06-no_content-leaks-to-the-caller-at-top-level) | `NO_CONTENT` leaks to the caller at top level | high | needs-decision |
| [R-07](#r-07-no_content-leaks-into-format-output) | `NO_CONTENT` leaks into `format` output | high | needs-decision |
| [R-08](#r-08-join-is-inconsistent-with-no_content-items) | `join` is inconsistent with `NO_CONTENT` items | medium | needs-decision |
| [R-09](#r-09-no_content-as-a-dynamic-name-attrsetget) | `NO_CONTENT` as a dynamic name (`attr`/`set`/`get`) | medium | needs-decision |
| [R-10](#r-10-no-default-value-mechanism) | No default-value mechanism | medium | needs-decision |
| [R-11](#r-11-zip-emits-python-tuples-and-inherits-python-zip-quirks) | `zip` emits Python tuples and inherits Python `zip` quirks | medium | needs-decision |
| [R-12](#r-12-join-of-an-empty-list-returns-) | `join` of an empty list returns `""` | low | needs-decision |
| [R-13](#r-13-output-aliases-input-data-shared-mutable-structures) | Output aliases input data (shared mutable structures) | medium | needs-decision |
| [R-14](#r-14-no-escape-for-a-literal-marker-key) | No escape for a literal marker (`$`) key | medium | needs-decision |
| [R-15](#r-15-set-scoping-is-subtle-and-undocumented) | `set` scoping is subtle and undocumented | medium | needs-decision |
| [R-16](#r-16-constant-vs-dynamic-parameters-are-inconsistent) | Constant vs dynamic parameters are inconsistent | low | needs-decision |
| [R-17](#r-17-include-has-no-cycledepth-protection-and-a-non-transon-default-error) | `include` has no cycle/depth protection; default loader raises `RuntimeError` | low | needs-decision |
| [R-18](#r-18-include-rule-has-no-docstring) | `include` rule has no docstring | low | accepted |
| [R-19](#r-19-docs-expr-with-values-ignores-this--underemphasized) | Docs: `expr` with `values` ignores `this` — underemphasized | low | accepted |
| [R-20](#r-20-python-version-policy-37-is-eol-no-312313-in-ci) | Python version policy: 3.7 is EOL, no 3.12/3.13 in CI | medium | accepted |
| [R-21](#r-21-broken-type-annotations-in-transformerspy) | Broken type annotations in `transformers.py` | low | accepted |
| [R-22](#r-22-contextderive-copies-all-variables-on-every-scope) | `Context.derive` copies all variables on every scope | low | needs-decision |

---

## Theme A — Error model & validation

### R-01. `and`/`or` operators are bitwise, not logical

**Status**: needs-decision · **Severity**: high · **Spec**: §12.1

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

### R-02. Raw Python exceptions escape the error model

**Status**: needs-decision · **Severity**: high · **Spec**: §12.6, §12.7 + audit

The contract is: `DefinitionError` = bad template, `TransformationError` = bad data.
In practice many code paths leak raw Python exceptions (all verified):

- `attr` only catches `KeyError`/`IndexError`; string-indexing a string or indexing
  a list with a non-int (including `NO_CONTENT`, see R-09) raises raw `TypeError`.
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

### R-03. Reserved-name guard is an `assert` — vanishes under `-O`

**Status**: accepted (fix is unambiguous) · **Severity**: high · **Spec**: §12.7 + audit

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

### R-04. No template validation; typos and ambiguity pass silently

**Status**: needs-decision · **Severity**: high · **Spec**: §12.13 + audit

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

### R-05. Error messages carry no template location

**Status**: needs-decision · **Severity**: medium · **Source**: audit

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

---

## Theme B — `NO_CONTENT` semantics

### R-06. `NO_CONTENT` leaks to the caller at top level

**Status**: needs-decision · **Severity**: high · **Spec**: §12.2

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

### R-07. `NO_CONTENT` leaks into `format` output

**Status**: needs-decision · **Severity**: high · **Spec**: §12.3

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

### R-08. `join` is inconsistent with `NO_CONTENT` items

**Status**: needs-decision · **Severity**: medium · **Spec**: §12.4

A `NO_CONTENT` item in `join.items` falls through all type checks and raises
`TransformationError: Can't join items` — unlike `map`/`object`/`file`/`filter`,
which skip.

**Impact if not fixed**: the natural pattern “join whichever of these optional
fields exist” crashes instead of degrading gracefully; authors work around it with
a redundant `filter`/`map` pass.

**Options**:

1. **(Recommended)** Filter `NO_CONTENT` items out before type dispatch — aligns
   `join` with the documented skip semantics. Edge effect: combines with R-12
   (all-items-missing → empty-list case hits the `""` quirk).
2. Keep raising, but with a precise message (“item 2 is NO_CONTENT”). Honest but
   keeps `join` the odd one out.

### R-09. `NO_CONTENT` as a dynamic name (`attr`/`set`/`get`)

**Status**: needs-decision · **Severity**: medium · **Source**: audit

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

### R-10. No default-value mechanism

**Status**: needs-decision · **Severity**: medium · **Source**: audit (feature gap)

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

---

## Theme C — JSON purity & data integrity

### R-11. `zip` emits Python tuples and inherits Python `zip` quirks

**Status**: needs-decision · **Severity**: medium · **Spec**: §12.8 + audit

`rule_zip` returns `list(zip(*items))` → a list of **tuples**. Tuples serialize via
`json.dumps` but are not lists: `join` of zipped rows raises `TransformationError`
(verified), strict equality/round-trip checks fail. Also inherited from Python
`zip`: strings are zipped character-wise, and non-iterable items raise raw
`TypeError` (→ R-02).

**Impact if not fixed**: violates the core promise “output is JSON”; `zip` results
are second-class values inside the engine itself.

**Options**:

1. **(Recommended)** Return lists of lists (`[list(row) for row in zip(*items)]`),
   raise `TransformationError` unless every item is a list. *Breaking* only for
   callers inspecting Python types of the output (tuples were never representable
   in JSON anyway) and for anyone deliberately zipping strings.
2. Lists of lists, but keep accepting any iterable (strings zip char-wise).
   Preserves a behavior that is almost certainly never intentional in JSON land.

### R-12. `join` of an empty list returns `""`

**Status**: needs-decision · **Severity**: low · **Spec**: §12.5

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

### R-13. Output aliases input data (shared mutable structures)

**Status**: needs-decision · **Severity**: medium · **Source**: audit

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

### R-14. No escape for a literal marker (`$`) key

**Status**: needs-decision · **Severity**: medium · **Spec**: §12.9

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

---

## Theme D — Language design & consistency

### R-15. `set` scoping is subtle and undocumented

**Status**: needs-decision · **Severity**: medium · **Spec**: §12.12

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

### R-16. Constant vs dynamic parameters are inconsistent

**Status**: needs-decision · **Severity**: low · **Source**: audit

Most rule parameters are templates (walked); a handful are read verbatim:
`expr.op`, `call.name`, `format.pattern`, `join.sep`, `chain.funcs` structure.
The rule docs don’t always say which. Verified failure: a template passed as
`join.sep` isn’t evaluated — it crashes with raw `AttributeError: 'dict' object
has no attribute 'join'` (also an R-02 instance).

**Impact if not fixed**: authors must memorize per-parameter rules; mistakes
surface as raw Python errors rather than “this parameter must be constant”.

**Options**:

1. **(Recommended)** Document constness per parameter (audit all `register_rule`
   param docs), and raise `DefinitionError` when a constant parameter receives a
   dict containing the marker. Keeps semantics, fixes diagnostics.
2. Make conservative parameters dynamic where harmless (`join.sep`,
   `format.pattern` could be walked). More uniform, but dynamic `expr.op` /
   `call.name` would make static validation (R-04) impossible — at minimum keep
   those constant.

### R-17. `include` has no cycle/depth protection; default loader raises `RuntimeError`

**Status**: needs-decision · **Severity**: low · **Source**: audit

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

### R-18. `include` rule has no docstring

**Status**: accepted (trivial, no decision needed) · **Severity**: low · **Spec**: §12.11

The only rule whose generated documentation is `doc: null`. Fix: write the
markdown docstring on `rule_include` covering loader delegation, the
value-only boundary (no variable/context crossing), and `NO_CONTENT` propagation.
Impact of not fixing: a documented feature is invisible on the docs site/playground.

### R-19. Docs: `expr` with `values` ignores `this` — underemphasized

**Status**: accepted (docs-only) · **Severity**: low · **Spec**: §12.10

Intended behavior, stated once in prose. Easy to misuse since every other mode
involves `this`. Fix: add a warning callout in the `values` parameter doc and a
corpus example demonstrating the ignored-context behavior. No code change.

---

## Theme E — Infrastructure & code quality

### R-20. Python version policy: 3.7 is EOL, no 3.12/3.13 in CI

**Status**: accepted (option 1, see Policy decisions) · **Severity**: medium · **Source**: audit

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

### R-21. Broken type annotations in `transformers.py`

**Status**: accepted (trivial, no decision needed) · **Severity**: low · **Source**: audit

`FileWriterType = Callable[[str, any], NoReturn]` uses the builtin function `any`
instead of `typing.Any`, and `NoReturn` (function never returns) instead of `None`
(returns nothing). Harmless at runtime, wrong under any type checker.
Fix: `Callable[[str, Any], None]`. Impact of not fixing: type checkers report
nonsense for anyone integrating the library; signals low typing hygiene.

### R-22. `Context.derive` copies all variables on every scope

**Status**: needs-decision · **Severity**: low · **Source**: audit

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

---

## Suggested sequencing

1. **No-decision fixes** (can start immediately): R-03, R-18, R-19, R-21.
2. **Error-model batch** (one minor release, loud changelog): R-01, R-02, R-09,
   R-16-diagnostics, R-17 — all convert crashes/silent wrongness into documented
   errors.
3. **NO_CONTENT batch**: R-06, R-07, R-08, R-10 — decide together, semantics
   interlock.
4. **Feature work**: R-04 (validation), R-05 (error paths), R-11, R-12, R-14.
5. **Policy/long-term**: R-13, R-15, R-20, R-22.
