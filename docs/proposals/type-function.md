# RFC: `type` value-type function (+ `include` loader propagation)

- **Status:** Implemented (2026-06-29) — both deliverables shipped (Roadmap R-26 `type` function and
  R-27 `include` `template_loader` propagation, both `done`). Engine-side counterpart of the
  `transon-blockly` *template-driven editor* pivot. The editor contract is recorded in
  `transon-blockly/docs/metadata-contract.md` §6.4; this RFC is the engine repo's home for the work
  that contract depends on.
- **Type:** New engine capability (additive on top of v0.1.x; **no behavior change to existing
  templates**).
- **Roadmap:** tracked as R-26 (`type` function) and R-27 (`include` `template_loader` propagation)
  in `docs/ROADMAP.md`, following R-23..R-25 (the editor-metadata export RFC).
- **Relationship to R-23..R-25:** independent and additive. Those delivered the editor-metadata
  export + `switch`/`cond` + `include` marker inheritance. This RFC adds the one remaining primitive
  the *generated codec* needs to walk arbitrary JSON.

## Why

The `transon-blockly` editor derives its encoder/decoder as Transon-template *projections* run by the
engine (no hand-written codec). The generated codec is a fixed **skeleton** that recurses over an
arbitrary document and, at every node, must dispatch on the node's **JSON type**:

- **object** → either a rule invocation (marker key → rule arm) or a literal object;
- **array** → recurse into items;
- **scalar** (string / number / boolean / null) → a literal leaf.

A Transon template can only dispatch via `switch`/`cond`, whose key/when expression **must not throw**
(branches are lazy, but the key is always evaluated; templates have no try/catch). The current engine
catalog offers **no total, non-throwing way to ask "what type is this value?"** — empirically verified
against the engine:

| Candidate | Result |
|---|---|
| `attr` / `map` / `filter` / `zip` / `join` / `expr` arithmetic | **throw** on the "wrong" type (e.g. `attr` on a non-dict, `map` on a scalar) — so they can't be used as a probe in a `switch` key |
| `call str` (the only *total* op) | **ambiguous**: a valid literal string `"{'a': 1}"` is byte-identical to `str()` of a real dict, so first-char dispatch misclassifies real documents |
| `expr == [this, str(this)]` | works (only a string equals its own `str()`), but only as **one half** of a convoluted two-step idiom: detect strings via the equality, then first-char `str()` on the remaining non-strings |

The two-step idiom is *correct* but verbose, and it is repeated at **every** dispatch point in **every**
projection template — a maintenance and readability cost that scales with the rule catalog (20 rules in
the editor's M2). A single `type` function collapses the whole dispatch to one clean `switch`.

This is the natural primitive the projection model needs, exactly parallel to `switch`/`cond` (R-23):
purely additive, an ordinary function, no new transformation language (`transon-blockly/SPEC.md`
§21.8), and no change to the meaning of any existing template.

## Deliverable 1 — `type` function (R-26, **required**)

A total function returning the JSON type name of any value:

```python
# transon/functions.py — registered exactly like str/int/float
def _json_type(value):
    if value is None:                 return 'null'
    if isinstance(value, bool):       return 'boolean'   # before int — bool subclasses int
    if isinstance(value, str):        return 'string'
    if isinstance(value, int):        return 'int'
    if isinstance(value, float):      return 'float'
    if isinstance(value, dict):       return 'object'
    if isinstance(value, list):       return 'array'
    raise DefinitionError(...)        # unreachable for JSON-shaped data

Transformer.register_function(
    'type', input_type='any', output_type='string',
    doc='Return the JSON type of a value: object/array/string/int/float/boolean/null.',
)(_json_type)
```

Invoked in a template via `{"<marker>": "call", "name": "type", "value": {"<marker>": "this"}}`, so the
codec skeleton dispatch becomes:

```json
{ "$": "switch", "key": { "$": "call", "name": "type", "value": { "$": "this" } },
  "cases": { "object": { ... }, "array": { ... } },
  "default": { ... scalar leaf ... } }
```

**Invariants (must hold, same as every built-in function):**

- **Total** — defined for every JSON value; never throws on well-formed data (this is the whole point;
  it is the one op a `switch` key can safely apply to an unknown node).
- **Pure**, stdlib-only, Python 3.9+, no mutation of input.
- Appears in `get_editor_metadata()`'s functions list (so the editor's `call.name` resolved-enum gains
  `type`) and in `get_functions()` docs — flows through the existing metadata-snapshot + parity
  machinery (the editor re-pins its snapshot).
- **Token set is the engine's to finalize.** Recommended: `object | array | string | int | float |
  boolean | null` (splitting `int`/`float` mirrors the existing `int`/`float` functions). The editor's
  dispatch only requires that `object`, `array`, and "any scalar" be distinguishable; the finer split
  is a free bonus.

## Deliverable 2 — `include` propagates `template_loader` (R-27, **recommended**)

The recursive codec skeleton is a single fragment that **self-`include`s** to recurse into child nodes.
Today a `Transformer` built by `rule_include` for a resolved sub-template inherits the include-stack and
`max_include_depth` but **not** the parent's `template_loader`, so the self-`include` fails to re-resolve
itself ("include not resolvable"). The editor's Node test adapter currently works around this by wrapping
each resolved include with `template_loader=loader` — but the **production in-browser host** (Pyodide,
`transon-blockly` AD-025) would need the identical patch.

**Proposal:** have `rule_include` propagate the active `template_loader` to the sub-`Transformer` it
runs (it already propagates the depth guard and the include-stack/marker). Additive; makes
recursive/self-referential codecs work without every host re-patching the loader.

**Design constraint — do not mutate the loaded instance; pass the inherited settings *through* the
loader.** Today `rule_include` configures the sub-`Transformer` by assigning to attributes of the
object returned by `template_loader` (`sub_transformer._include_stack = stack`,
`sub_transformer.max_include_depth = ...`, `sub_transformer.marker = ...`). Extending that pattern to
add `sub_transformer.template_loader = t.template_loader` would be the obvious move, but it makes the
problem worse:

- the loader may legitimately return a **cached/shared** `Transformer`, so post-hoc mutation leaks the
  caller's include-stack, depth, marker, and loader into other users of that instance;
- the propagated state is set *after* construction, so `validate()` and any constructor-time invariants
  never see it; and
- it reaches past the public API into a private attribute (`_include_stack`).

Instead, the inherited include-context becomes **constructor input** that flows to the sub-`Transformer`
via the loader, so the instance is born correctly configured and `rule_include` mutates nothing it does
not own:

- Widen the loader contract from `Callable[[str], Transformer]` to `loader(name, context=...)`: `include`
  **always** passes an `IncludeContext` dataclass carrying the parent's `template_loader`, resolved
  `marker`, `max_include_depth`, and current include-stack. `context` is optional in the loader signature
  (defaulted) so a loader may still be invoked standalone, but the engine always supplies it.
- Provide a small built-in helper (`IncludeContext.transformer(template, *, marker=None, **kwargs)`) so
  dict-backed loaders don't re-thread every field — the common loader body becomes
  `return context.transformer(templates[name])`.
- Add the include-stack as a real constructor parameter alongside the existing
  `template_loader` / `marker` / `max_include_depth`, so none of these need post-construction assignment.
- **No arity-detection / legacy fallback.** An earlier draft kept a `Callable[[str], Transformer]`
  compatibility branch; it is dropped as redundant. Every loader simply accepts the optional `context`.
  This is a small, explicit **breaking change** to the loader contract (a `template_loader` must accept
  the `context` keyword) in exchange for a single, mutation-free code path.

Net effect: recursive codecs work out of the box, shared/cached loader results stay safe, and the marker
/ depth / stack inheritance that already exists is expressed as construction rather than mutation, with
one uniform loader-call path.

## Out of scope (declined / deferred)

- **`keys` / `has` predicates.** Surface-checking (detecting undeclared params) and variant matching can
  be expressed with `map` + the pre-derived variant signatures; a dedicated `keys`/`has` would only be a
  readability nicety. Deferred until proven necessary in M2 — **not** part of this RFC.
- **Making accessors (`attr` etc.) non-throwing.** Rejected: changing throw-on-type-mismatch to a silent
  default would mask real `TransformationError`s. `type`-based dispatch removes the need (the codec only
  enters the object arm on a confirmed object), so accessors keep their current strict semantics.
- **No new transformation language** (`transon-blockly/SPEC.md` §21.8): `type` is an ordinary function;
  nothing here adds path syntax, an expression DSL, or `eval`/`apply`.
