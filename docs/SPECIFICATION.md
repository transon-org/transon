# transon — Engine Specification

> **Audience**: developers (human or AI) maintaining and extending the `transon` library itself.
> **Status**: descriptive — this document specifies the engine *as implemented* (v0.0.7).
> Deliberate design questions and suspected accidental behaviors are collected in
> [§12 Known issues & design questions](#12-known-issues--design-questions).

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
| `transon/rules.py` | All 20 built-in rules, registered via `@Transformer.register_rule` |
| `transon/operators.py` | Operators for the `expr` rule (registered via `register_operator`) |
| `transon/functions.py` | Functions for the `call` rule (registered via `register_function`) |
| `transon/docs.py` | Documentation generator: harvests docstrings + test cases into JSON |
| `transon/tests/` | **Example corpus**: table-driven test cases that double as documentation |
| `tests/` | Plain pytest tests for engine mechanics (errors, extension, docs generation) |
| `.github/workflows/dev.yml` | CI: pytest + coverage on Python 3.7–3.11 |
| `.github/workflows/release.yml` | PyPI publish on `v*` tags |

Packaging is Poetry (`pyproject.toml`). Runtime dependencies: none (stdlib only;
`importlib-metadata` backport for Python 3.7).

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
There is **no escaping mechanism** for emitting a literal dict that contains the marker
key — the only workaround is the `object` rule (`{"$": "object", "key": "$", "value": ...}`).

A rule invocation dict carries its parameters as sibling keys of the marker:

```json
{"$": "attr", "name": "x"}
```

Rule parameters are themselves templates (walked recursively), except where a rule
explicitly requires a constant (e.g. `expr.op`, `call.name`, `format.pattern`,
`join.sep`, `chain.funcs` list structure).

### 2.2 Context

`Context` (in `transformers.py`) is a linked chain of scopes. Each context holds:

- `this` — the current value (root context: the transformation input).
- Iteration properties — `item`, `index` (lists), `key`, `value`, `index` (dicts);
  only present inside `map`/`filter` iterations.
- User variables — arbitrary names written by the `set` rule, read by `get`.
- `parent` — the context this one was derived from.

`context.derive(**props)` creates a child: it **copies all data from the parent** and
overlays the new props. `set` writes into the data dict of the exact context object it
executes in. Consequences (all verified against the implementation):

- Variables flow **downward only**: a `derive()` performed *after* a `set` carries the
  variable; the parent's own dict is untouched by sets in derived contexts. So a `set`
  inside a `map` item or inside a non-first `chain` step is invisible once that scope
  ends.
- `walk_dict`/`walk_list` pass the **same context object** to all siblings, so a `set`
  executed directly at one key of a literal dict is visible to later-evaluated sibling
  keys (insertion order). The first func of a `chain` also runs in the caller's
  context, so a `set` there escapes into the caller's scope; subsequent funcs run in
  derived contexts and their sets do not.
- `get` only checks the current context's data dict — but ancestor variables are
  present there by copying at derive time, so lookup effectively covers the whole chain.

The names `this`, `item`, `key`, `value`, `index` are **reserved**: `Context.__contains__`,
`__getitem__`, `__setitem__` assert against them, so they cannot be used as variable
names with `set`/`get` (violation raises `AssertionError`, not a transon error type).

### 2.3 NO_CONTENT — the "no value" sentinel

`Transformer.NO_CONTENT` is a singleton `NoContent` instance representing the absence
of a value (distinct from JSON `null`/Python `None`). Semantics:

- **Producers**: `attr` (missing key/index), `get` (undefined variable), `file` (always),
  `include` (when the included template yields `NO_CONTENT`).
- **Absorption**: `NoContent.__getitem__` returns `self`, so further `attr` lookups on
  a missing value stay `NO_CONTENT` instead of raising.
- **Consumers (skip/filter behavior)**:
  - `map`: items (or key/value pairs) that evaluate to `NO_CONTENT` are omitted.
  - `object`: returns `{}` if key or value is `NO_CONTENT`.
  - `file`: skips writing if name or content is `NO_CONTENT`.
  - `filter`: a condition evaluating to `NO_CONTENT` excludes the element.
- **No special handling elsewhere** — see §12 for places where the sentinel leaks
  (top-level result, `format`, `join`, comparisons).

In the documentation/test corpus, a top-level `NO_CONTENT` result is treated as `None`
(see `transon/tests/base.py::TableDataBaseCase.test`).

### 2.4 Error model

| Exception | Meaning | Raised when |
|---|---|---|
| `DefinitionError` | The template is malformed | Unknown rule/operator/function name; missing required rule parameter (`Transformer.require`); `attr` with neither `name` nor `names`; `map` with no valid parameter combination |
| `TransformationError` | The template is valid but input data is incompatible | `map`/`filter` over a non-iterable (not list/dict); `join` over mixed-type items |

Both are exported from the package root. Errors are raised lazily during
`transform()` — there is no template validation phase.

---

## 3. The `Transformer` class

### 3.1 Public API

```python
Transformer(
    template,                      # JSON-like structure
    *,
    file_writer=no_file_writer,    # Callable[[str, Any], None] — used by the `file` rule
    template_loader=no_template_loader,  # Callable[[str], Transformer] — used by `include`
    marker='$',                    # rule marker key
)
transformer.transform(data) -> output   # may return Transformer.NO_CONTENT
```

The default `template_loader` raises `RuntimeError`; the default `file_writer` silently
discards writes.

### 3.2 Registries and extension

Three registries exist, all class-level dicts with decorator-based registration:

| Registry | Decorator | Used by rule | Signature of registered callable |
|---|---|---|---|
| `_rules` | `register_rule(name, **param_docs)` | (dispatch) | `(t: Transformer, template: dict, context: Context) -> Any` |
| `_operators` | `register_operator(name)` | `expr` | unary `(a)` or binary `(a, b)` |
| `_functions` | `register_function(name)` | `call` | `(*args) -> Any` |

`register_rule` attaches metadata to the function: `__rule_name__` (the rule name) and
`__rule_params__` (a `dict[str, str]` of parameter-name → markdown documentation). This
metadata feeds the documentation pipeline (§5).

**Subclass isolation**: `Transformer.__init_subclass__` resets `_rules`, `_operators`,
`_functions` to empty dicts on every subclass. Lookup (`get_rule`/`get_operator`/
`get_function`) walks the MRO, so subclasses *inherit* base registrations and may
*shadow* them, but registrations on a subclass never affect the base class or sibling
subclasses. `get_rules()` returns all rules visible to a class with MRO-based dedupe
(closest definition wins).

```python
class MyTransformer(Transformer): pass

@MyTransformer.register_rule('my_rule', param="Docs for `param`.")
def my_rule(t: Transformer, template, context: Context):
    """Markdown docstring — becomes the rule's documentation."""
    value = t.walk(t.require(template, 'param'), context)
    ...
```

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

Accessing an iteration property outside its scope raises `KeyError` (no transon error type).

### 4.2 Variables

| Rule | Parameters | Semantics |
|---|---|---|
| `set` | `name` (dynamic) | Stores `context.this` under `name` in the *current* context; returns `context.this` (pass-through, usable as a tap inside `chain`) |
| `get` | `name` (dynamic) | Returns the stored value or `NO_CONTENT` if undefined |

### 4.3 Data access — `attr`

Parameters (mutually exclusive; one required, else `DefinitionError`):

- `name` (dynamic): single key or numeric index into `context.this`.
- `names` (dynamic): list of keys/indexes, applied sequentially (deep path).

Missing key (`KeyError`) or index out of range (`IndexError`) → `NO_CONTENT`.
Other lookup failures (e.g. `TypeError` indexing a string with a string) propagate raw.

### 4.4 Structure builders

| Rule | Parameters | Semantics |
|---|---|---|
| `object` | `key`, `value` (both required, dynamic) | Single-pair dict `{key: value}`; `{}` if either side is `NO_CONTENT`. For dynamically-named attributes. |
| `map` | exactly one of: `item` \| `items` \| `key`+`value` | Iterates `context.this` (list or dict). `item`: one output element per input element → list. `items`: template yields a *list* of elements per input element, concatenated → list. `key`+`value`: → dict. `NO_CONTENT` results are skipped. Each iteration derives a sub-context with `this`=element plus iteration props. |
| `filter` | `cond` (required, dynamic) | Keeps elements where `cond` is truthy (and not `NO_CONTENT`). Preserves container type: list→list, dict→dict. |
| `zip` | `items` (required, dynamic) | `list(zip(*items))` — transposes a list of lists. Produces Python **tuples** in the output. |
| `join` | `items` (required, dynamic), `sep` (constant, strings only, default `""`) | Type-homogeneous concatenation: all-strings → `sep.join`; all-lists → flatten one level; all-dicts → merged dict (later keys win). Mixed types → `TransformationError`. |
| `chain` | `funcs` (required; list of templates) | Function composition: walks each template in order, each result becomes `this` of a derived context for the next. `chain(f1, f2, f3)(x) == f3(f2(f1(x)))`. |

### 4.5 Computation

| Rule | Parameters | Semantics |
|---|---|---|
| `expr` | `op` (required, constant), optionally `value` (dynamic) or `values` (dynamic) | No param → unary `op(this)`. `value` → binary `op(this, value)`. `values` → `reduce(op, values)` (**`this` is ignored**). |
| `call` | `name` (required, constant), optionally `value` or `values` (dynamic) | No param → `fn(this)`. `value` → `fn(value)`. `values` → `fn(*values)`. `this` is ignored when params given. |
| `format` | `pattern` (required, constant), `value` (optional, dynamic; defaults to `this`) | Python `str.format`. List value → positional unpack `pattern.format(*v)`; dict value → keyword unpack `pattern.format(**v)`; otherwise single argument. |

### 4.6 Side effects & composition

| Rule | Parameters | Semantics |
|---|---|---|
| `file` | `name`, `content` (both required, dynamic) | Calls the configured `file_writer(name, content)`. Skipped if either is `NO_CONTENT`. Always returns `NO_CONTENT` (so `map` over `file` yields `[]`). |
| `include` | `name` (required, dynamic) | Loads a sub-`Transformer` via the configured `template_loader` and runs it against `context.this`. Variables/context do **not** cross the boundary — only the value. Sub-result `NO_CONTENT` is propagated as this transformer's `NO_CONTENT`. |

### 4.7 Built-in operators (`expr`)

Each operator has a mnemonic and a code-style alias mapping to the same Python
`operator` module function:

| Mnemonic | Alias | Python impl | Note |
|---|---|---|---|
| `lt le eq ne ge gt` | `< <= == != >= >` | `operator.lt` … | comparisons |
| `add sub mul div mod` | `+ - * / %` | `operator.add` …, `truediv` for `div` | `+` also concatenates strings/lists |
| `and or not` | `&& \|\| !` | `operator.and_`, `or_`, `not_` | **bitwise**, not logical — see §12 |

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
poetry install --with dev
poetry run pytest -v --cov=transon --cov-config=.coveragerc --cov-report term-missing .
```

CI (`.github/workflows/dev.yml`) runs this matrix on Python 3.7–3.11 and uploads
coverage to Codecov (3.11 only). Coverage excludes `transon/tests/*` (`.coveragerc`).
Keep code compatible with **Python 3.7** (no 3.8+ syntax: no walrus in hot paths is
fine, but no `match`, no `|` type unions, etc.).

---

## 7. Checklist: adding a new rule

1. Implement in `transon/rules.py` (or a subclass for experimental work):
   - decorate with `@Transformer.register_rule('<name>', <param>="<markdown doc>", ...)`;
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

- Version lives **only** in `pyproject.toml` (`tool.poetry.version`); runtime reads it
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
- `transform()` never mutates the input data or the template.
- Registry lookups respect MRO; subclass registries never pollute the base class.
- `NO_CONTENT` skipping semantics in `map`/`object`/`file`/`filter` are part of the
  public contract (relied on by the corpus, e.g. `test_no_content.py`).
- Iteration order: dict iteration follows insertion order (Python ≥3.7 guarantee).

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
`zip` produces `[("a",1), ("b",2)]` → chain derives context with that as `this` →
`map` iterates, each pair becomes `this`/`item` in a sub-context → `attr` with numeric
names indexes the tuple → output `{"a": 1, "b": 2}`.

---

## 12. Known issues & design questions

Current behavior is documented above; the items below look accidental or unresolved.
**Do not "fix" silently** — each needs a deliberate decision (and a changelog entry,
since templates in the wild may rely on current behavior).

1. **`and`/`or`/`&&`/`||` are bitwise, not logical.** They map to `operator.and_`/
   `or_` (`&`/`|`). On `bool` inputs the result is correct; on ints it's bitwise
   (`6 and 3` → `2`), and on other types it may `TypeError`. No short-circuiting either
   (irrelevant for pre-evaluated values, but semantically surprising).
2. **`NO_CONTENT` leaks at the top level.** `transform()` can return the raw
   `NoContent` instance to callers (the test harness maps it to `None`; library users
   get the sentinel object, which is not JSON-serializable).
3. **`NO_CONTENT` leaks into `format`** — formatting a missing value interpolates the
   object repr (`<transon.transformers.NoContent object at …>`) instead of skipping.
4. **`join` with a `NO_CONTENT` item** raises `TransformationError` instead of skipping
   the item (inconsistent with `map`/`object` semantics).
5. **`join` of an empty `items` list returns `""`** even when lists/dicts were intended
   (the all-strings branch wins vacuously).
6. **`attr` only catches `KeyError`/`IndexError`** — e.g. string-indexing a string
   raises a raw `TypeError`; arguably should be `NO_CONTENT` or `TransformationError`.
7. **Iteration accessors outside `map` raise raw `KeyError`**; reserved-name violations
   in `set`/`get` raise `AssertionError`. Both bypass the transon error model.
8. **`zip` emits Python tuples**, not lists — JSON-serializable via `json.dumps` but
   not round-trippable as JSON arrays in strict pipelines.
9. **No literal-`$` escape**: data containing the marker key as a plain key cannot be
   expressed in a template except via the `object` rule (or changing the marker).
10. **`expr` with `values` ignores `context.this`** — documented, but easy to misuse;
    the rule doc says "current context value is ignored" so this is intended.
11. **`include` rule has no docstring** — the only rule missing user-facing docs
    (`get_rules_docs` returns `doc: null` for it).
12. **`set` mutates the shared context** — whether a variable is visible to sibling
    templates depends on the exact context object the `set` executed in (e.g. directly
    at a dict key or as the *first* `chain` func: visible to later siblings; inside a
    later `chain` step or a `map` item: not). Subtle and undocumented for template
    authors.
13. **No template validation phase** — `DefinitionError` surfaces only when the faulty
    branch is actually walked; dead branches with typos pass silently.
