# Transon — Template Language Reference

> **Audience**: template authors (human or agent). This document is the **cross-cutting**
> semantics of the Transon template language: the evaluation model, scoping, the
> `NO_CONTENT` propagation model, the error taxonomy, the `expr`/`call` machinery, and
> composition patterns. It deliberately contains **no per-rule reference**: what each
> individual rule, operator, or function does — its parameters, modes, and edge cases —
> lives in that entry's own documentation, exported by the engine
> (`transon.docs.get_all_docs()` / `transon.metadata.get_editor_metadata()`) and rendered
> on the [docs site](https://transon-org.github.io/). Entity names appear here only as
> illustrations. Executable examples live in the example corpus shipped with those same
> exports.

## Templates and the marker

A template is any JSON value. The engine walks it top-down and rebuilds it node by node;
each node is handled by its JSON type:

- a **list** → walk every element, return a new list;
- a **dict containing the marker key** (default `"$"`) → a **rule invocation** (see below);
- a **dict without the marker** → walk every value, return a new dict with the same keys;
- any **scalar** (string, number, boolean, `null`) → copied through unchanged.

A template that contains no markers is therefore reproduced as a deep copy of itself —
rules are the only thing that injects data.

A dict is a rule *only* when it contains the marker key; the marker's value names the
rule and the sibling keys are the rule's parameters:

```json
{"$": "attr", "name": "x"}
```

Rule parameters are themselves templates and are walked recursively, so rules nest
arbitrarily — this is why even arithmetic is expressed as nested rules rather than a
string mini-language. A handful of parameters are documented as **constant** (for
example an operator name): those are read verbatim, never walked.

The marker is configurable per transformation (`marker=` on the transformer). To emit a
literal dict that really contains the marker key — data that would otherwise be read as
a rule invocation — use the `object` rule's `fields` mode, whose keys are emitted
verbatim while its values stay templates; its single-pair `key`/`value` mode also
produces one literal key.

When one template `include`s another, the sub-template inherits the parent's marker by
default, so a template tree written against the default marker stays consistent across
`include` boundaries; the loader may pin a different marker explicitly.

## Context and scoping

Evaluation carries a **context** — a linked chain of scopes. Each context holds:

- `this` — the current value (in the root context: the transformation input);
- iteration properties — `item`, `index` over lists; `key`, `value`, `index` over
  dicts — present only inside scopes derived by the iterating rules (`map`, `filter`);
- user variables — arbitrary names written by `set`, read by `get`;
- a link to the **parent** scope it was derived from.

Rules that carry a value into a sub-template derive a **child scope**: each `map`/
`filter` iteration derives one per element (exposing the iteration properties), and
each `chain` step after the first derives one whose `this` is the previous step's
result. The context accessor rules (`this`, `parent`, `item`, `key`, `value`, `index`)
read these slots; each is valid only where its slot exists, and using one outside its
valid scope is a template mistake (`DefinitionError`).

Variables flow **downward only**. The rules of visibility, in decreasing surprise:

| Where a `set` runs | Its variable is visible to |
|---|---|
| any scope | descendant scopes derived *after* the `set` |
| directly at a key/element of a literal dict/list | later-evaluated siblings in that dict/list (they share one scope; dict key / list index order matters) |
| the **first** func of a `chain` | the caller's scope — later `chain` funcs *and* later siblings outside the `chain` |
| a later `chain` func, a `map`/`filter` iteration | only that derived scope and its descendants |
| anywhere | **never** the parent scope after the derived scope ends; **never** an `include`d sub-template (that is a separate transformation — only the value crosses the boundary) |

Refactoring pitfall: wrapping a step in `chain`, reordering dict keys, or moving a
`set` can change visibility with no error — consult the table.

The names `this`, `item`, `key`, `value`, and `index` are **reserved** and cannot be
used as variable names with `set`/`get` (violation raises `DefinitionError`).

## The NO_CONTENT model

`NO_CONTENT` is the language's "no value" sentinel — distinct from JSON `null`. `null`
is a value you can store and emit; `NO_CONTENT` means *there is nothing here*, and the
language is built so that missing data disappears from the output instead of blowing up
or leaving `null` holes.

- **Where it comes from**: lookups that miss (an absent attribute or path, an undefined
  variable), aggregations left with nothing (a `join` whose items all vanished), rules
  that never produce a value (`file`), and sub-transforms that themselves produced
  nothing (`include`).
- **Skip, don't emit**: container rules *omit* a `NO_CONTENT` piece rather than emitting
  `null` — as illustrations: `map` drops the item, `object` omits the entry, `filter`
  excludes the element, `join` leaves the item out. The exact treatment each rule
  applies is stated in that rule's documentation.
- **Defaults stop propagation**: rules that can miss accept an optional `default`
  template, evaluated *instead of* producing `NO_CONTENT` — the tool for "this value,
  or X if missing" at the point of lookup.
- **Absorption**: looking further into a missing value stays missing — a deep `attr`
  path over an absent branch yields `NO_CONTENT`, it does not raise.
- **Falsiness**: `NO_CONTENT` is falsy, so logical operators can express fallbacks —
  e.g. a `chain` ending in `expr` `or` with a substitute value. Rules that *test* for
  absence use identity, not truthiness: `false`, `0`, and `""` are values, not absence.
- **The top level**: `transform()` never returns the raw sentinel by default — a
  template that evaluates to `NO_CONTENT` returns `None` (configurable via the
  `no_content` argument).

## Error model

Template failures are typed by *whose mistake they are*:

| Exception | Meaning | Representative causes |
|---|---|---|
| `DefinitionError` | The **template** is malformed — fix the template | unknown rule/operator/function name; a missing required parameter; unknown parameters; ambiguous or incomplete mutually-exclusive parameter groups; a reserved variable name used with `set`/`get`; a context accessor used outside its valid scope; a structural parameter with the wrong JSON shape |
| `TransformationError` | The template is valid but the **input data** does not fit it | iterating a non-iterable; joining mixed-type items; an operator applied to incompatible operand types; a function rejecting its arguments; a format pattern referencing a missing key; an `include` chain exceeding the depth limit |

By default errors are raised **lazily**, when the failing node is actually walked — a
typo in a branch the data never reaches will not surface. Opt in to **static
validation** (`validate=True`, or calling `validate()`) to check the template's
structure up front, with no input data: unknown rules, unknown or missing parameters,
ambiguous parameter combinations, and invalid literal operator/function names all raise
`DefinitionError` immediately.

Both error types carry the **template location** where the failure occurred — a path of
dict keys, list indices, rule names, and parameter names:

```text
value is not iterable: 'not-a-list'
  at template → pipeline → chain → funcs[0] → map
```

Which specific conditions each rule raises is part of that rule's documentation.

## Expressions and calls

Operators (the `expr` rule) and functions (the `call` rule) share one application
model; these semantics hold across **every** operator and function, so they live here.
The catalog of what exists — each operator's types and each function's signature — is
in the `expr` `op` / `call` `name` parameter docs and the engine exports.

**Operator application** (`expr`) has three modes:

- no value parameter → **unary**: `op(this)`;
- `value` → **binary**: `op(this, value)` — the current value is the left operand;
- `values` → **reduction**: `reduce(op, values)` pairwise over the evaluated list —
  and the current value is **ignored**; include `{"$": "this"}` as a list item if the
  reduction should involve it. `values` must be a non-empty list — an empty reduction
  has no seed and raises `DefinitionError` (see the empty-collection caveat under
  composition patterns).

**Type behavior** follows Python semantics: `+` concatenates strings and lists as well
as adding numbers; comparisons work on like types; the logical operators use
truthiness and return an *operand*, not necessarily a boolean. An operator applied to
incompatible operand types raises `TransformationError`.

**Function application** (`call`) mirrors the modes: no parameter → `fn(this)`;
`value` → `fn(value)`; `values` → `fn(*values)` (multi-argument call). The current
value is ignored whenever a parameter is given. Built-in functions convert their
documented failure modes into `TransformationError` — a well-formed template never
leaks a raw Python exception from a bad argument. A few functions are documented as
**total** (they accept any well-formed JSON value and never raise); totality is stated
per function in the catalog.

**`NO_CONTENT` in expressions**: operators and functions do not skip it. A
`NO_CONTENT` operand is simply falsy (useful in `and`/`or` fallbacks) or an
incompatible argument (an error) — stop the propagation earlier with a `default` if
the operand may be missing.

## Composition patterns

The language has no aggregate primitives beyond what composition provides — a handful
of rules cover everything *because* they compose. The canonical shapes:

- **Pipeline**: `chain` walks its steps in order, each result becoming `this` for the
  next — the backbone for "extract, then reshape, then format" templates.
- **Reshape**: `map` (over a list or dict) with a nested `object`/`attr` template body;
  `filter` before it to drop elements; `zip` to transpose parallel lists.
- **Compute**: nested `expr` rules — arithmetic is a tree of rules, not a string.
- **Reuse**: `include` runs a named sub-template against the current value. Only the
  value crosses the boundary (no variables, no iteration properties); the marker is
  inherited by default; nested includes are depth-limited.
- **Aggregate from primitives**: a count is `length` (or a `map` to `1`s reduced with
  `add`); a flatten is the `flatten` function (or `map` in its `items` mode). **Mind
  the empty collection**: an `expr` `values` reduction over an empty list is a
  `DefinitionError` (no seed), an empty `join` yields `NO_CONTENT` (use its `default`),
  while `sum` of an empty array is `0` — pick the primitive whose empty-case behavior
  matches the intent.

A worked end-to-end flow — pairing two parallel lists into a dict:

```json
{
  "$": "chain",
  "funcs": [
    {"$": "zip", "items": [{"$": "attr", "name": "keys"},
                            {"$": "attr", "name": "values"}]},
    {"$": "map", "key": {"$": "attr", "name": 0},
                  "value": {"$": "attr", "name": 1}}
  ]
}
```

Input `{"keys": ["a","b"], "values": [1,2]}` → the root context's `this` is the input →
`zip` produces `[["a",1], ["b",2]]` → `chain` derives a context with that as `this` →
`map` iterates, each pair becoming `this`/`item` in a per-element scope → `attr` with
numeric names indexes each pair → output `{"a": 1, "b": 2}`.
