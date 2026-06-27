# transon — Engine Specification

> **Audience**: developers (human or AI) maintaining and extending the `transon` library itself.
> **Status**: descriptive — this document specifies the engine *as implemented* (v0.0.9).
> Deliberate design questions and suspected accidental behaviors are tracked in
> [`docs/ROADMAP.md`](ROADMAP.md) (see [§12](#12-known-issues--design-questions)).

`transon` is a homogeneous JSON-to-JSON template engine. A `Transformer` is constructed
from a *template* (itself a valid JSON structure) and applied to JSON *input data*,
producing JSON *output*. It is inspired by XSLT and JsonLogic.

```
                    ┌─────────────────┐
                    │  JSON Template  │
                    └────────┬────────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌───────────────┐
│  JSON Input  ├────►     transon     ├────►  JSON Output  │
└──────────────┘    └─────────────────┘    └───────────────┘
```

---

## 1. Repository layout

| Path | Purpose |
|---|---|
| `transon/transformers.py` | Engine core: `Transformer`, `Context`, `NoContent`, error types |
| `transon/rules.py` | All 22 built-in rules, registered via `@Transformer.register_rule` |
| `transon/operators.py` | Operators for the `expr` rule (registered via `register_operator`) |
| `transon/functions.py` | Functions for the `call` rule (registered via `register_function`) |
| `transon/docs.py` | Documentation generator: harvests docstrings + test cases into JSON |
| `transon/metadata.py` | Editor-metadata export (`get_editor_metadata`) for the visual editor (§5.1) |
| `transon/tests/` | **Example corpus**: table-driven test cases that double as documentation |
| `tests/` | Plain pytest tests for engine mechanics (errors, extension, docs generation) |
| `.github/workflows/dev.yml` | CI: pytest + coverage on Python 3.9–3.13 (uv) |
| `.github/workflows/release.yml` | PyPI publish on `v*` tags |

Packaging is uv / PEP 621 (`pyproject.toml`, `uv.lock`). Runtime dependencies: none
(stdlib only).

---

## 2. Core concepts

### 2.1 Templates and the marker

A template is any JSON value. The engine walks it recursively (`Transformer.walk`):

- **list** → walk each element, return a new list (`walk_list`).
- **dict containing the marker key** (default `"$"`) → this is a **rule invocation**;
  dispatch to the registered rule named by the marker's value (`walk_rule`).
- **dict without the marker** → walk each value, return a new dict with the same keys (`walk_dict`).
- **anything else** (scalar) → returned as-is (`walk_scalar`).

The marker is configurable per `Transformer` instance (`marker=` constructor kwarg).
To emit a literal dict that contains the marker key, use the `object` rule in `fields`
mode (`{"$": "object", "fields": {"$": ...}}`): the keys of `fields` are emitted
verbatim while the values are walked as templates (R-14). The single-pair form
(`{"$": "object", "key": "$", "value": ...}`) also works for one literal key.

A rule invocation dict carries its parameters as sibling keys of the marker:

```json
{"$": "attr", "name": "x"}
```

Rule parameters are themselves templates (walked recursively), except where a rule
explicitly requires a constant (e.g. `expr.op`, `call.name`, `chain.funcs` list
structure).

### 2.2 Context

`Context` (in `transformers.py`) is a linked chain of scopes. Each context holds:

- `this` — the current value (root context: the transformation input).
- Iteration properties — `item`, `index` (lists), `key`, `value`, `index` (dicts);
  only present inside `map`/`filter` iterations.
- User variables — arbitrary names written by the `set` rule, read by `get`.
- `parent` — the context this one was derived from.

`context.derive(**props)` creates a child linked via `parent`: it stores only the
new props (e.g. `this`, iteration slots). Reads of user variables walk the parent
chain; the first `set` in a derived scope materializes inherited variables into the
local dict so writes stay isolated. `set` writes into the data dict of the exact
context object it executes in.

#### Variable scoping (`set` / `get`)

Template authors should treat these rules as the contract (R-15):

| Where `set` runs | Visible to |
|---|---|
| Descendant scopes (`derive()` after the `set`) | Yes — visible via parent-chain lookup; first `set` in a child snapshots inherited vars |
| Later sibling keys/items in the same literal dict/list | Yes — siblings share one context object; order matters |
| Earlier sibling keys/items in the same literal dict/list | No — already evaluated |
| First func of a `chain` | Caller's scope, later `chain` funcs, and later siblings outside the `chain` |
| Later `chain` func, `map`/`filter` iteration, etc. | Only that derived scope and its descendants |
| Parent scope after a derived scope ends | No |
| `include` sub-template | No — separate `transform()` |

Consequences (all verified against the implementation):

- Variables flow **downward only**: a `derive()` performed *after* a `set` carries the
  variable; the parent's own dict is untouched by sets in derived contexts. So a `set`
  inside a `map` item or inside a non-first `chain` step is invisible once that scope
  ends.
- `walk_dict`/`walk_list` pass the **same context object** to all siblings, so a `set`
  executed directly at one key of a literal dict is visible to later-evaluated sibling
  keys (insertion order). The first func of a `chain` also runs in the caller's
  context, so a `set` there escapes into the caller's scope; subsequent funcs run in
  derived contexts and their sets do not.
- `get` walks the current context's data dict, then the parent chain for undefined
  names — so ancestor variables are visible without eager copying on `derive()`. The
  first `set` in a derived scope materializes inherited variables locally.

Refactoring pitfall: wrapping a step in `chain`, reordering dict keys, or moving a
`set` can change visibility with no error — consult the table above.

The names `this`, `item`, `key`, `value`, `index` are **reserved**
(`Context.RESERVED_NAMES`): `Context.__contains__`, `__getitem__`, `__setitem__`
check against them, so they cannot be used as variable names with `set`/`get`
(violation raises `DefinitionError`).

### 2.3 NO_CONTENT — the "no value" sentinel

`Transformer.NO_CONTENT` is a singleton `NoContent` instance representing the absence
of a value (distinct from JSON `null`/Python `None`). Semantics:

- **Producers**: `attr` (missing key/index), `get` (undefined variable), `file` (always),
  `include` (when the included template yields `NO_CONTENT`), `join` (when there are no
  items to join). Optional `default` on `attr`, `get`, `format`, `include`, and `join`
  returns a substitute instead of `NO_CONTENT`.
- **Falsiness**: `NoContent` is falsy in boolean context (`bool()`, `expr` `and`/`or`),
  so logical operators can fall back from `NO_CONTENT` (e.g. `chain` of `join` then
  `expr` `or` with a fallback value). Rules that test for absence still use identity
  (`is NO_CONTENT`), not truthiness.
- **Absorption**: `NoContent.__getitem__` returns `self`, so further `attr` lookups on
  a missing value stay `NO_CONTENT` instead of raising.
- **Consumers (skip/filter behavior)**:
  - `map`: items (or key/value pairs) that evaluate to `NO_CONTENT` are omitted.
  - `object`: in `key`/`value` mode returns `{}` if key or value is `NO_CONTENT`;
    in `fields` mode omits each entry whose value is `NO_CONTENT`.
  - `file`: skips writing if name or content is `NO_CONTENT`.
  - `filter`: a condition evaluating to `NO_CONTENT` excludes the element.
  - `join`: items that evaluate to `NO_CONTENT` are omitted before concatenation; when
    no items remain the result is `NO_CONTENT` unless `default` is provided.
- **`format`**: returns `NO_CONTENT` when the formatting value (or any unpacked list
  element or dict key/value) is `NO_CONTENT`, unless `default` is provided.
- **Top-level `transform()`**: by default maps a top-level `NO_CONTENT` result to
  `None` via the `no_content` parameter (see §3.1). Pass `Transformer.NO_CONTENT`
  as `no_content` to receive the raw sentinel.

### 2.4 Error model

| Exception | Meaning | Raised when |
|---|---|---|
| `DefinitionError` | The template is malformed | Unknown rule/operator/function name; missing required rule parameter (`Transformer.require` or `Transformer.validate()`); unknown rule parameters; ambiguous or incomplete mutually-exclusive parameter groups (`validate()`); `attr` with neither `name` nor `names`; `map` with no valid parameter combination; reserved variable name (`this`, `item`, `key`, `value`, `index`) used with `set`/`get`; iteration accessors (`item`, `key`, `value`, `index`) or `parent` used outside their valid scope; `expr`/`call` with a non-list or empty `values` parameter; non-list `chain.funcs` (`validate()`); `include` with no configured `template_loader` (default loader) |
| `TransformationError` | The template is valid but input data is incompatible | `map`/`filter` over a non-iterable (not list/dict); `join` over mixed-type items; `attr` lookup with an incompatible index type; `zip` over non-iterable items; `expr` operator applied to incompatible operand types; `call` with incompatible argument types; `format` pattern referencing a missing key or index; `set`/`get` when a dynamic `name` evaluates to `NO_CONTENT`; `include` depth limit exceeded (nested include chain too deep) |

Both are exported from the package root. By default, errors are raised lazily during
`transform()` — there is no automatic validation. Opt in with `Transformer.validate()`
or `Transformer(..., validate=True)` for a static walk that raises `DefinitionError`
for unknown rules, unknown rule parameters, missing required parameters, ambiguous
mutually-exclusive parameter combinations, and invalid literal operator/function names
(see §3.4).

`DefinitionError` and `TransformationError` messages include the template location
where the failure occurred (a path of dict keys, list indices, rule names, and rule
parameter names), for example:

```
value is not iterable: 'not-a-list'
  at template → pipeline → chain → funcs[0] → map
```

---

## 3. The `Transformer` class

### 3.1 Public API

```python
Transformer(
    template,                      # JSON-like structure
    *,
    validate=False,                # if True, run validate() before use
    file_writer=no_file_writer,    # Callable[[str, Any], None] — used by the `file` rule
    template_loader=no_template_loader,  # Callable[[str], Transformer] — used by `include`
    marker='$',                    # rule marker key
    max_include_depth=50,          # nested `include` depth limit (see `include` rule)
)
transformer.transform(data, no_content=None, *, copy_output=False) -> output
transformer.validate()            # static template check; raises DefinitionError
```

`no_content` controls the value returned when the template produces `NO_CONTENT`.
The default is `None` (JSON-friendly). Pass any other value as a substitute (e.g. a
marker string), or pass `Transformer.NO_CONTENT` to receive the raw sentinel.
Inside rule evaluation, rules still produce and compare `Transformer.NO_CONTENT` as
before; substitution applies only at the `transform()` boundary.

**Output aliasing**: `transform()` never mutates the input data or the template, but
rules that pass a value straight through (`this`, `attr`, `get`, `item`, …) return a
*reference* into the input rather than a copy. Consequently, mutating the returned
structure afterwards mutates the original input — the "never mutates input" invariant
holds only until the caller touches the result. This is intentional (no per-rule
copying overhead in the common case). Callers who post-process the output should pass
`copy_output=True`, which `copy.deepcopy`-es the result exactly once at the
`transform()` boundary so the returned value shares no mutable structure with the
input. The default (`copy_output=False`) is unchanged. (Roadmap R-13, option 2.)

The default `template_loader` raises `DefinitionError`; the default `file_writer` silently
discards writes.

### 3.2 Registries and extension

Three registries exist, all class-level dicts with decorator-based registration:

| Registry | Decorator | Used by rule | Signature of registered callable |
|---|---|---|---|
| `_rules` | `register_rule(name, **param_docs)` | (dispatch) | `(t: Transformer, template: dict, context: Context) -> Any` |
| `_operators` | `register_operator(name)` | `expr` | unary `(a)` or binary `(a, b)` |
| `_functions` | `register_function(name)` | `call` | `(*args) -> Any` |

`register_rule` attaches metadata to the function: `__rule_name__` (the rule name),
`__rule_params__` (a `dict[str, str]` of parameter-name → markdown documentation),
and `__rule_schema__` (the `variants` tuple — one complete required-parameter shape
per mutually exclusive form). This metadata feeds the documentation pipeline (§5) and
static validation (§3.4).

**Subclass isolation**: `Transformer.__init_subclass__` resets `_rules`, `_operators`,
`_functions` to empty dicts on every subclass. Lookup (`get_rule`/`get_operator`/
`get_function`) walks the MRO, so subclasses *inherit* base registrations and may
*shadow* them, but registrations on a subclass never affect the base class or sibling
subclasses. `get_rules()` returns all rules visible to a class with MRO-based dedupe
(closest definition wins).

```python
class MyTransformer(Transformer): pass

@MyTransformer.register_rule(
    'my_rule',
    _variants=[{'param'}],
    param="Docs for `param`.",
)
def my_rule(t: Transformer, template, context: Context):
    """Markdown docstring — becomes the rule's documentation."""
    value = t.walk(t.require(template, 'param'), context)
    ...
```

### 3.4 Static template validation

`Transformer.validate()` walks the template without input data and raises
`DefinitionError` when:

- a rule name is not registered;
- a rule invocation includes parameters not declared in `register_rule`;
- required parameters are missing;
- mutually exclusive parameter groups overlap (e.g. `attr` with both `name` and
  `names`, `map` with both `item` and `key`/`value`, `expr`/`call` with both
  `value` and `values`);
- a parameter group is partially present (e.g. `map` with `key` but no `value`);
- a structural parameter has the wrong JSON shape — a `MAPPING` parameter that is
  not an object, a `LIST`/`ARMS` parameter that is not an array, or an `ARMS`
  object missing one of its declared required slots (e.g. a `cond` arm missing
  `when`/`then`);
- a `constant` parameter bound to a closed domain is a string literal outside that
  domain (e.g. `expr.op`/`call.name` naming an unknown operator/function).

Validation is **fully generic**: it is driven entirely by per-parameter descriptors
declared at the rule source (below) and contains no special-casing by rule or
parameter name.

Pass `validate=True` to the constructor to validate at construction time. Validation
is opt-in and non-breaking: `transform()` behavior is unchanged when validation is
not used. Nested templates inside rule parameters are validated recursively; dynamic
parameter values that are not rule invocations are not evaluated.

Rule authors declare validation metadata via `register_rule` keyword arguments:

- `_variants=[{'op'}, {'op', 'value'}, {'op', 'values'}]` — a list of sets, the
  closed set of valid complete parameter shapes; exactly one must match. Each variant
  is the set of parameters that shape requires. Parameters shared by **all** variants
  are the always-required ones (their absence reports `… property is required`);
  parameters that distinguish variants are the mutually exclusive groups (overlap or
  partial presence is rejected). A single-element list such as `[{'name'}]` means one
  required parameter; an empty variant `[set()]` (the default) means no required
  parameters.
- `_constants={'op': Domain.OPERATOR}` — marks a parameter **constant** (`ParamKind`
  read verbatim, never walked) and binds its closed enum `Domain`
  (`OPERATOR`/`FUNCTION`), used for membership validation and for the
  editor-metadata `options` (§5.1).
- `_containers={'fields': ContainerType.MAPPING}` — declares a **structural**
  parameter whose shape validation descends generically: `MAPPING` (literal keys,
  template values) or `LIST` (template elements).
- `_arms={'cases': arm(_variants=[{'when', 'then'}], when=..., then=...)}` — declares
  an **`ARMS`** parameter: an ordered list of objects whose slots are declared the
  *same way as parameters* (slot docstrings plus `_variants`/`_constants`/
  `_containers`) and validated by the same per-parameter routine.

The kind, container type, and domain are `enum.Enum` types (`ParamKind`,
`ContainerType`, `Domain`), exported from `transon`. Optional parameters need no
flag — they are any declared parameter that appears in no `_variants` entry. A
parameter with no descriptor defaults to a dynamic template (`ParamKind.DYNAMIC`,
`ContainerType.TEMPLATE`).

### 3.3 Rule-author helpers

- `t.require(template, name)` — return `template[name]` or raise `DefinitionError`
  naming the rule and the missing parameter.
- `t.walk(sub_template, context)` — recursively evaluate a parameter (parameters are
  templates too; call this for every dynamic parameter).
- `t.NO_CONTENT` — produce/compare the no-value sentinel.
- `context.derive(this=..., ...)` — create a child scope before walking sub-templates.
- `t.write_file(name, content)` — delegate to the configured `file_writer`.
- `t.template_loader(name)` — obtain a sub-`Transformer` by name.

---

## 4. Built-in rule reference

All rules live in `transon/rules.py`. "Dynamic" parameters are walked as templates;
"constant" parameters are read verbatim.

### 4.1 Context accessors (no parameters)

| Rule | Returns | Valid scope |
|---|---|---|
| `this` | `context.this` — current value | anywhere |
| `parent` | `context.parent.this` — value of previous scope | any non-root scope |
| `item` | current list element | inside `map`/`filter` over a list |
| `index` | 0-based iteration index | inside `map`/`filter` |
| `key` | current dict key | inside `map`/`filter` over a dict |
| `value` | current dict value | inside `map`/`filter` over a dict |

Accessing `parent` in the root context or an iteration property outside its scope
raises `DefinitionError`.

### 4.2 Variables

| Rule | Parameters | Semantics |
|---|---|---|
| `set` | `name` (dynamic) | Stores `context.this` under `name` in the *current* context; returns `context.this` (pass-through, usable as a tap inside `chain`). Raises `TransformationError` if `name` evaluates to `NO_CONTENT`. Scoping: see §2.2 (variable scoping table). |
| `get` | `name` (dynamic), `default` (optional, dynamic) | Returns the stored value from the *current* context (ancestor variables resolved via parent-chain lookup). Returns `NO_CONTENT` if undefined. Raises `TransformationError` if `name` evaluates to `NO_CONTENT`. When `default` is provided, returns its evaluation instead of `NO_CONTENT`. Scoping: see §2.2. |

Examples for each scoping case live in `transon/tests/test_set.py` (docs-site examples).

### 4.3 Data access — `attr`

Parameters (mutually exclusive; one required, else `DefinitionError`):

- `name` (dynamic): single key or numeric index into `context.this`.
- `names` (dynamic): list of keys/indexes, applied sequentially (deep path).
- `default` (optional, dynamic): returned instead of `NO_CONTENT` when the lookup misses.

Missing key (`KeyError`) or index out of range (`IndexError`) → `NO_CONTENT` (or
`default` when provided).
When `name` or any path segment in `names` evaluates to `NO_CONTENT` → `NO_CONTENT`
(uniform regardless of container type).
Other lookup failures (e.g. `TypeError` indexing a string with a string) →
`TransformationError`.

### 4.4 Structure builders

| Rule | Parameters | Semantics |
|---|---|---|
| `object` | exactly one of: `key`+`value` \| `fields` | `key`+`value` (dynamic): single-pair dict `{key: value}`; `{}` if either side is `NO_CONTENT`. For dynamically-named attributes. `fields`: literal mapping whose keys are emitted verbatim (including the marker `$` — the canonical literal-marker-key escape, R-14) and whose values are walked as templates; entries with a `NO_CONTENT` value are omitted. |
| `map` | exactly one of: `item` \| `items` \| `key`+`value` | Iterates `context.this` (list or dict). `item`: one output element per input element → list. `items`: template yields a *list* of elements per input element, concatenated → list. `key`+`value`: → dict. `NO_CONTENT` results are skipped. Each iteration derives a sub-context with `this`=element plus iteration props. |
| `filter` | `cond` (required, dynamic) | Keeps elements where `cond` is truthy (and not `NO_CONTENT`). Preserves container type: list→list, dict→dict. |
| `zip` | `items` (required, dynamic) | Transposes iterables like Python's `zip`: each output row is a **list** (`[list(row) for row in zip(*items)]`). Non-iterable items → `TransformationError`. |
| `join` | `items` (required, dynamic), `sep` (dynamic, strings only, default `""`), `default` (optional, dynamic) | Type-homogeneous concatenation: all-strings → `sep.join`; all-lists → flatten one level; all-dicts → merged dict (later keys win). Items that evaluate to `NO_CONTENT` are omitted before concatenation. When no items remain → `NO_CONTENT` (or `default` when provided). Mixed types → `TransformationError`. `sep` must evaluate to a string when joining strings. |
| `chain` | `funcs` (required; list of templates) | Function composition: walks each template in order, each result becomes `this` of a derived context for the next. `chain(f1, f2, f3)(x) == f3(f2(f1(x)))`. |

### 4.5 Computation

| Rule | Parameters | Semantics |
|---|---|---|
| `expr` | `op` (required, constant), optionally `value` (dynamic) or `values` (dynamic) | No param → unary `op(this)`. `value` → binary `op(this, value)`. `values` → `reduce(op, values)` (**`this` is ignored**). |
| `call` | `name` (required, constant), optionally `value` or `values` (dynamic) | No param → `fn(this)`. `value` → `fn(value)`. `values` → `fn(*values)`. `this` is ignored when params given. |
| `format` | `pattern` (required, dynamic), `value` (optional, dynamic; defaults to `this`), `default` (optional, dynamic) | Python `str.format`. `pattern` must evaluate to a string. Returns `NO_CONTENT` when the formatting value (or any unpacked list element or dict key/value) is `NO_CONTENT`, unless `default` is provided. List value → positional unpack `pattern.format(*v)`; dict value → keyword unpack `pattern.format(**v)`; otherwise single argument. |
| `switch` | `key` (required, dynamic), `cases` (required, `mapping`), `default` (optional, dynamic) | **Lazy** equality dispatch: evaluates `key`, then walks **only** the matching entry of `cases` (a literal-keyed mapping of templates). No match — including `key` → `NO_CONTENT` — evaluates `default` if present, else `NO_CONTENT`. Non-selected cases are never walked. |
| `cond` | `cases` (required, `arms`), `default` (optional, dynamic) | **Lazy** ordered conditional (subsumes `if`/`else`): `cases` is an ordered list of `{when, then}` arms. Walks each `when` in order; the first truthy one selects its `then` (the only `then` walked). A `when` of `NO_CONTENT` is falsy. No match → `default` if present, else `NO_CONTENT`. |

### 4.6 Side effects & composition

| Rule | Parameters | Semantics |
|---|---|---|
| `file` | `name`, `content` (both required, dynamic) | Calls the configured `file_writer(name, content)`. Skipped if either is `NO_CONTENT`. Always returns `NO_CONTENT` (so `map` over `file` yields `[]`). |
| `include` | `name` (required, dynamic), `default` (optional, dynamic) | Loads a sub-`Transformer` via the configured `template_loader` and runs it against `context.this`. Variables/context do **not** cross the boundary — only the value. When the loaded sub-`Transformer` still uses the default marker (`$`), it **inherits the parent transformer's marker**; a sub-template that pins a non-default marker keeps it (there is no per-call `marker` argument). Sub-result `NO_CONTENT` is propagated as this transformer's `NO_CONTENT` (or `default` when provided). Nested includes are tracked by name; exceeding `max_include_depth` (constructor parameter, default 50) raises `TransformationError` with the include chain in the message. |

### 4.7 Built-in operators (`expr`)

Each operator has a mnemonic and a code-style alias mapping to the same Python
`operator` module function:

| Mnemonic | Alias | Python impl | Note |
|---|---|---|---|
| `lt le eq ne ge gt` | `< <= == != >= >` | `operator.lt` … | comparisons |
| `add sub mul div mod` | `+ - * / %` | `operator.add` …, `truediv` for `div` | `+` also concatenates strings/lists |
| `and or not` | `&& \|\| !` | logical `and`/`or`/`not` | Python truthiness; returns operands, not always `bool` |

### 4.8 Built-in functions (`call`)

`str`, `int`, `float` — the Python builtins, registered directly.

---

## 5. Documentation pipeline

The documentation (and the playground at https://transon-org.github.io/) is **generated
from source artifacts**; nothing is hand-maintained separately:

1. **Rule docs** — rule function docstrings (markdown, may embed plantuml).
2. **Parameter docs** — `**params` kwargs of `register_rule`.
3. **Examples** — the table-driven test corpus in `transon/tests/` (§6).

`transon/docs.py` assembles these:

- `get_test_cases()` imports every module under `transon.tests` and collects all
  `TableDataBaseCase` subclasses having complete `template`/`data`/`result`.
- Cases are matched to rules by **tags**: tag `"<rule>"` attaches the case as a
  rule-level example; tag `"<rule>:<param>"` attaches it as a parameter-level example.
- `get_all_docs()` returns the complete JSON document:

```json
{
  "version": "<package version>",
  "doc": "<Transformer class docstring>",
  "rules": [
    {
      "rule": {"name": "...", "doc": "..."},
      "examples": [{"name", "doc", "template", "data", "result"}, ...],
      "params": [
        {"param": {"name": "...", "doc": "..."},
         "examples": [...]}
      ]
    }
  ]
}
```

- `python -m transon.docs` prints this JSON, lists cases whose docstring still contains
  `TBD`, and prints the case count. Note: the version lookup requires the package to be
  installed (`pip install -e .` or via Poetry), otherwise `PackageNotFoundError`.

### 5.1 Editor-metadata export

`transon/metadata.py` provides `get_editor_metadata()` — a dedicated, versioned export,
**separate from the docs API**, that emits projection-ready metadata for the
`transon-blockly` visual editor (engine facts only; no Blockly shapes). It is **split**
into a lean structural `catalog` (consumed by the editor's generators) and an
`examples/docs` payload (descriptions + tagged examples), joined by `name`:

```json
{
  "metadata_version": "<schema version>",
  "engine_version": "<package version>",
  "catalog": {
    "rules": [{"name", "params": [{"name", "kind", "options?"}], "variants": [...]}],
    "operators": [{"name", "alternative", "kind", "types", "result"}],
    "functions": [{"name", "input", "output"}]
  },
  "docs": {"rules": [...], "operators": [...], "functions": [...]}
}
```

- **Variant signatures** (`derive_variants`) are pre-computed in Python from
  `_required`/`_modes`: one entry per valid mutually-exclusive parameter shape, each
  listing its ordered visible params flagged `required` (the empty mode yields a valid
  zero-extra-parameter variant). Consumers read these directly.
- Per-parameter **`kind`** (`dynamic`/`constant`) comes from the rule source; a
  `constant` parameter bound to a closed domain carries its resolved **`options`**
  (`expr.op` → operator names + aliases, `call.name` → function names).
- `python -m transon.metadata` prints this JSON.
- `docs.template_loader` makes every test case's template `include`-able by its class
  name (e.g. `{"$": "include", "name": "MapListsToDict"}`).

---

## 6. Testing conventions

Two distinct test trees, both run by plain `pytest` from the repo root:

### 6.1 `transon/tests/` — the example corpus (shipped with the package)

Table-driven cases subclassing `TableDataBaseCase` (`transon/tests/base.py`):

```python
class MapDictToDictItems(base.TableDataBaseCase):
    """
    Iterates over input dictionary and produces dictionary with keys and values swapped.
    """                                      # ← user-facing docs; never leave "TBD"
    tags = ['map:key', 'map:value', 'key', 'value']   # ← binds example to rules/params
    template = {'$': 'map', 'key': {'$': 'value'}, 'value': {'$': 'key'}}
    data = {'a': 'd', 'b': 'e'}
    result = {'d': 'a', 'e': 'b'}
```

Mechanics:

- `__init_subclass__` auto-registers every subclass; `test()` asserts
  `Transformer(template).transform(data) == result` (with `NO_CONTENT` mapped to `None`).
- Classes that omit `template`/`data`/`result` are **abstract bases** (skipped via
  `unittest.SkipTest`) — used to share a template across multiple data/result cases
  (see `base_attr.py`, `base_join.py`).
- `tags` is mandatory. Use `"<rule>"` and/or `"<rule>:<param>"` strings; every tag makes
  the case appear as an example in the generated docs for that rule/parameter.
- Docstrings are user-facing documentation. `python -m transon.docs` reports any case
  whose doc contains `TBD`.
- `conftest.py` registers assert-rewriting for `base.py`.

### 6.2 `tests/` — engine mechanics (not shipped)

Plain pytest functions for behavior that doesn't fit the table format: error raising
(`DefinitionError`/`TransformationError`), registry extension/isolation, `file_writer`
mocking, `get_all_docs()` smoke test.

### 6.3 Running

```shell
uv sync --dev
uv run pytest -v --cov=transon --cov-config=.coveragerc --cov-report term-missing .
```

CI (`.github/workflows/dev.yml`) runs this matrix on Python 3.9–3.13 and uploads
coverage to Codecov (3.11 only). Coverage excludes `transon/tests/*` (`.coveragerc`).
Requires **Python 3.9+**.

---

## 7. Checklist: adding a new rule

1. Implement in `transon/rules.py` (or a subclass for experimental work):
   - decorate with `@Transformer.register_rule('<name>', _variants=[...], <param>="<markdown doc>", ...)`;
   - write a markdown docstring (it *is* the documentation);
   - use `t.require()` for mandatory params, `t.walk()` for dynamic params;
   - return `t.NO_CONTENT` for "no value", raise `DefinitionError` for template
     mistakes, `TransformationError` for data mismatches;
   - honor `NO_CONTENT` in inputs where skipping is the sensible semantics.
2. Add table-driven example cases in `transon/tests/test_<name>.py`:
   - at least one case tagged `"<name>"` and one per parameter tagged `"<name>:<param>"`
     (parameter examples are what the docs page shows under each parameter);
   - meaningful docstrings, realistic data.
3. Add negative tests in `tests/` for error paths if applicable.
4. Update the expected rule-name set in `tests/test_transformers.py::test_get_rules`.
5. Run `python -m transon.docs` (package must be installed) — verify the rule renders,
   no `TBD` reported.
6. Run the full suite: `pytest .`

Adding an operator/function: register in `operators.py`/`functions.py`, update the
markdown tables inside `expr.op` / `call.name` parameter docs in `rules.py`, and add
tagged example cases.

---

## 8. Versioning & release

- Version lives **only** in `pyproject.toml` (`[project].version`); runtime reads it
  via `importlib.metadata`.
- Release: push tag `v*` → `.github/workflows/release.yml` builds with Poetry and
  publishes to PyPI.

---

## 9. Design principles (from README, binding for new work)

1. **Flexibility & extensibility** — new rules/operators/functions must be pluggable
   via the registries; no hardcoded dispatch.
2. **Valid JSON structure** — templates must remain expressible as pure JSON. No
   string-embedded DSLs (path expressions, inline arithmetic). Complex behavior is
   built by *composing* rules.
3. **Composability** — rules should consume/produce values so they can nest under
   `chain`, `map`, etc.
4. **Marker-based** — rule detection happens only via the marker key; everything else
   is literal data.

---

## 10. Invariants to preserve

- A template containing **no marker dicts** is reproduced as-is (deep copy by walking).
- Rule parameters are templates: any parameter documented as "dynamic" must go through
  `t.walk()`.
- `transform()` never mutates the input data or the template. Pass-through rules
  (`this`/`attr`/`get`/`item`/…) return references into the input, so the *output* may
  alias input substructures; callers that mutate the result must pass
  `copy_output=True` (deep-copies the result once) to avoid corrupting their input
  (§3.1, Roadmap R-13).
- Registry lookups respect MRO; subclass registries never pollute the base class.
- `NO_CONTENT` skipping semantics in `map`/`object`/`file`/`filter` are part of the
  public contract (relied on by the corpus, e.g. `test_no_content.py`).
- Iteration order: dict iteration follows insertion order (Python 3.7+ guarantee).

---

## 11. Engine data flow (reference example)

Template:

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

Input `{"keys": ["a","b"], "values": [1,2]}` → root context `this=input` →
`zip` produces `[["a",1], ["b",2]]` → chain derives context with that as `this` →
`map` iterates, each pair becomes `this`/`item` in a sub-context → `attr` with numeric
names indexes the tuple → output `{"a": 1, "b": 2}`.

---

## 12. Known issues & design questions

Suspected accidental behaviors and open design questions are tracked exclusively in
[`docs/ROADMAP.md`](ROADMAP.md) (items `R-01`…`R-22`), each with impact analysis,
fix options, and a decision status. This document describes current behavior only.

**Do not "fix" quirky behavior silently** — every behavior change needs an explicit
decision recorded in the roadmap (flip the item's status) and a changelog entry,
since templates in the wild may rely on current behavior.
