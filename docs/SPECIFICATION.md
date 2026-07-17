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
| `transon/rules.py` | All 23 built-in rules, registered via `@Transformer.register_rule` |
| `transon/operators.py` | Operators for the `expr` rule (registered via `register_operator`) |
| `transon/functions.py` | Functions for the `call` rule (registered via `register_function`) |
| `transon/docs.py` | Documentation generator: harvests docstrings + test cases into JSON |
| `transon/metadata.py` | Editor-metadata export (`get_editor_metadata`) for the visual editor (§5.1) |
| `transon/reference.py` | Language Reference export (`get_language_reference`) — serves the packaged `LANGUAGE.md` (§5.2) |
| `transon/resources/LANGUAGE.md` | Packaged copy of `docs/LANGUAGE.md` (ships in the wheel/sdist; a test asserts identity) |
| `docs/LANGUAGE.md` | **Template Language Reference** — author-facing, cross-cutting semantics (canonical, hand-edited) |
| `transon/tests/` | **Example corpus**: table-driven test cases that double as documentation |
| `tests/` | Plain pytest tests for engine mechanics (errors, extension, docs generation) |
| `.github/workflows/dev.yml` | CI: pytest + coverage on Python 3.9–3.13 (uv) |
| `.github/workflows/release.yml` | PyPI publish on `v*` tags |

Packaging is uv / PEP 621 (`pyproject.toml`, `uv.lock`). Runtime dependencies: none
(stdlib only).

---

## 2. Core concepts

> **Author-facing semantics live in [`docs/LANGUAGE.md`](LANGUAGE.md)** — the Template
> Language Reference (evaluation model, scoping, the `NO_CONTENT` model, the error
> taxonomy, `expr`/`call` machinery, composition patterns), also served by
> `transon.reference.get_language_reference()` (§5.2). This section keeps only the
> **engine-internal** view: which code implements those semantics and the
> implementation invariants a contributor must preserve.

### 2.1 Template walk

`Transformer.walk` dispatches by JSON type: **list** → `walk_list`, **dict with the
marker key** → `walk_rule` (registry dispatch), **dict without** → `walk_dict`,
**scalar** → `walk_scalar`. The marker is per-instance (`marker=` constructor kwarg).
Rule parameters are walked recursively except parameters registered as constants
(`ParamKind.CONSTANT`, e.g. `expr.op`, `call.name`). The literal-marker escape is the
`object` rule's `fields` mode (R-14).

### 2.2 Context

`Context` (in `transformers.py`) is a linked chain of scopes holding `this`, the
iteration slots, user variables, and a `parent` link. Implementation invariants
(R-15/R-22 — the observable scoping model built on them is specified in the Language
Reference, "Context and scoping"):

- `context.derive(**props)` stores **only** the new props (copy-on-write); reads of
  user variables walk the parent chain; the **first** `set` in a derived scope
  materializes inherited variables locally so writes stay isolated.
- `set` writes into the data dict of the exact context object it executes in;
  `walk_dict`/`walk_list` pass the **same** context object to all siblings, and the
  first func of a `chain` runs in the caller's context — these two facts produce the
  documented sibling-order and first-chain-func visibility.
- The names `this`, `item`, `key`, `value`, `index` are **reserved**
  (`Context.RESERVED_NAMES`): `__contains__`/`__getitem__`/`__setitem__` check against
  them and raise `DefinitionError`.

### 2.3 NO_CONTENT — the "no value" sentinel

`Transformer.NO_CONTENT` is a singleton `NoContent` instance representing the absence
of a value (distinct from JSON `null`/Python `None`). Implementation facts:

- `NoContent.__bool__` is `False` (falsiness powers `expr` `and`/`or` fallbacks) and
  `NoContent.__getitem__` returns `self` (absorption for deep `attr` paths). Rules
  that test for absence use **identity** (`is NO_CONTENT`), never truthiness.
- The skip-don't-emit propagation model is specified in the Language Reference ("The
  NO_CONTENT model"); each rule's exact treatment is stated in that rule's docstring
  and is part of the public contract (§10).
- `transform()` substitutes a top-level `NO_CONTENT` via its `no_content` parameter
  (default `None`, §3.1); inside evaluation rules always see the raw sentinel.

### 2.4 Error model

`DefinitionError` (malformed template) and `TransformationError` (valid template,
incompatible data) are both defined in `transformers.py` and exported from the package
root. The taxonomy as an author experiences it is in the Language Reference ("Error
model"); which conditions each rule raises is in that rule's docstring. Engine-side
contract:

- Errors are raised **lazily** during `transform()`; static checking is the opt-in
  `validate()` walk (§3.4).
- Every message is routed through `format_error_message`, which appends the template
  location (`at template → …`) from the template-path `ContextVar` maintained by
  `walk` — new raise sites must use `t.definition_error` / `t.transformation_error`
  (or `format_error_message`) so the path is never lost.

---

## 3. The `Transformer` class

### 3.1 Public API

```python
Transformer(
    template,                      # JSON-like structure
    *,
    validate=False,                # if True, run validate() before use
    file_writer=no_file_writer,    # Callable[[str, Any], None] — used by the `file` rule
    template_loader=no_template_loader,  # loader(name, context=IncludeContext) -> Transformer — used by `include`
    marker='$',                    # rule marker key
    max_include_depth=50,          # nested `include` depth limit (see `include` rule)
    include_stack=None,            # inherited include chain; set by `include` propagation
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

Per-rule behavior is **not** specified here (ownership principle, RFC 0008): each
rule's semantics — parameters, modes, edge cases, `NO_CONTENT` treatment, error
conditions — live in its registration docs in `transon/rules.py` (docstrings +
`register_rule` param kwargs), which every export carries (`get_all_docs()`,
`get_editor_metadata()['docs']`) and the docs site renders. Operator and function
catalogs live the same way in `transon/operators.py` / `transon/functions.py` and the
`expr` `op` / `call` `name` parameter docs. Cross-cutting semantics (evaluation model,
scoping, `NO_CONTENT`, errors, `expr`/`call` machinery) are in
[`docs/LANGUAGE.md`](LANGUAGE.md).

### Recursion budget

Walking one level of template nesting consumes a bounded, small number of Python
call-stack frames — one core recursion frame per node (no `walk`/`_walk`-style
doubling). Because the generated `transon-blockly` editor codec self-`include`s once
per document node (AD-030), its reachable nesting depth is governed by this budget,
not by `max_include_depth`. The engine therefore transforms self-`include`ing
templates at nesting depths well past the editor's deepest generator (`G_encode`,
depth 41) within CPython's default recursion limit (1000). Exceeding
`max_include_depth` MUST surface as the `include` depth-limit `TransformationError`,
never a raw `RecursionError`. (Roadmap R-32.)

---

## 5. Documentation pipeline

The documentation (and the playground at https://transon-org.github.io/) is **generated
from source artifacts**; the one hand-written artifact is
[`docs/LANGUAGE.md`](LANGUAGE.md) (the Template Language Reference — cross-cutting
semantics only, no per-entity sections; served packaged via §5.2, its section shape
pinned by `tests/test_reference.py`). Everything else is harvested:

1. **Rule docs** — rule function docstrings (markdown, may embed plantuml).
2. **Parameter docs** — `**params` kwargs of `register_rule`.
3. **Examples** — the table-driven test corpus in `transon/tests/` (§6).

`transon/docs.py` assembles these:

- `get_test_cases()` imports every module under `transon.tests` and collects all
  `TableDataBaseCase` subclasses having complete `template`/`data`/`result`.
- Cases are matched to rules by **tags**: tag `"<rule>"` attaches the case as a
  rule-level example; tag `"<rule>:<param>"` as a parameter-level example; tag
  `"op:<alternative>"` / `"func:<name>"` as an operator-/function-level example; the
  tier tags `"worked-example"` / `"recipe"` place a case in a curated tier.
- Examples are **normalized** (Roadmap R-31): the flat `examples` block serializes
  every corpus case **exactly once** (`get_example_corpus()`), and every other
  `examples` field is an ordered list of `name` **references** into it. The tag join
  is engine-owned — consumers resolve names against the corpus and never re-derive
  membership from tag conventions. Only the `errors` block stays inline (error cases
  live in a different shape and appear exactly once).
- `get_all_docs()` returns the complete JSON document:

```json
{
  "version": "<package version>",
  "doc": "<Transformer class docstring>",
  "examples": [
    {"name": "...", "doc": "...", "template": ..., "data": ..., "result": ..., "tags": [...]},
    ...
  ],
  "worked_examples": ["<case name>", ...],
  "recipes": ["<case name>", ...],
  "errors": [
    {"name", "doc", "template", "data", "error", "error_type", "action"}, ...
  ],
  "rules": [
    {
      "rule": {"name": "...", "doc": "..."},
      "examples": ["<case name>", ...],
      "params": [
        {"param": {"name": "...", "doc": "..."},
         "examples": ["<case name>", ...]}
      ]
    }
  ],
  "operators": [
    {"operator": {"name", "alternative", "kind", "types", "result", "doc"},
     "examples": ["<case name>", ...]}
  ],
  "functions": [
    {"function": {"name", "input", "output", "doc"},
     "examples": ["<case name>", ...]}
  ]
}
```

- Corpus invariants (tested in `tests/test_docs.py` / `tests/test_metadata.py`): case
  names are unique; every name referenced anywhere resolves to exactly one corpus
  entry; every corpus case is reachable from at least one reference list; curated
  cases carry **only** their tier tag and never appear in reference galleries;
  reference cases never carry a tier tag.
- `python -m transon.docs` prints this JSON, lists cases whose docstring still contains
  `TBD`, and prints the case count. Note: the version lookup requires the package to be
  installed (`pip install -e .` or via Poetry), otherwise `PackageNotFoundError`.

### 5.1 Editor-metadata export

`transon/metadata.py` provides `get_editor_metadata()` — a dedicated, versioned export,
**separate from the docs API**, that emits projection-ready metadata for the
`transon-blockly` visual editor (engine facts only; no Blockly shapes). It is **split**
into a lean structural `catalog` (consumed by the editor's generators) and an
`examples/docs` payload (descriptions + the flat example corpus), joined by `name`:

```json
{
  "metadata_version": "<schema version>",
  "engine_version": "<package version>",
  "catalog": {
    "rules": [{"name",
               "params": [{"name", "kind", "options?", "container?", "arm?"}],
               "variants": [...]}],
    "operators": [{"name", "alternative", "kind", "types", "result"}],
    "functions": [{"name", "input", "output"}]
  },
  "docs": {
    "examples": [
      {"name": "...", "doc": "...", "template": ..., "data": ..., "result": ..., "tags": [...]},
      ...
    ],
    "rules": [{"name", "description",
               "params": [{"name", "description", "examples": ["<case name>", ...], "arms?"}],
               "examples": ["<case name>", ...]}],
    "operators": [{"name", "doc", "examples": ["<case name>", ...]}],
    "functions": [{"name", "doc", "examples": ["<case name>", ...]}],
    "worked_examples": ["<case name>", ...],
    "recipes": ["<case name>", ...]
  }
}
```

- **Variant signatures** (`derive_variants`) are pre-computed in Python from
  `_required`/`_modes`: one entry per valid mutually-exclusive parameter shape, each
  listing its ordered visible params flagged `required` (the empty mode yields a valid
  zero-extra-parameter variant). Consumers read these directly.
- Per-parameter **`kind`** (`dynamic`/`constant`) comes from the rule source; a
  `constant` parameter bound to a closed domain carries its resolved **`options`**
  (`expr.op` → operator names + aliases, `call.name` → function names). Structural
  facts are emitted when not the default: `container` (`mapping`/`list`/`arms`;
  omitted for `template`) and, for `arms` params, the `arm: {required, params}` slot
  schema (the docs payload mirrors it with per-slot `arms` descriptions).
- Examples are **normalized** exactly as in `get_all_docs()` (§5, Roadmap R-31):
  `docs.examples` is the flat corpus (each case once, with `tags`); all other
  `examples` fields and the curated `worked_examples` / `recipes` tiers are ordered
  `name` references into it. The same corpus invariants apply.
- `python -m transon.metadata` prints this JSON.
- `docs.template_loader` makes every test case's template `include`-able by its class
  name (e.g. `{"$": "include", "name": "MapListsToDict"}`).

### 5.2 Language Reference export

`transon/reference.py` provides `get_language_reference()` — a dedicated, versioned
export (RFC 0008, R-36) serving the packaged `LANGUAGE.md` offline:

- Shape: `{reference_version, engine_version, format: "markdown", content, sections}`.
  `content` is the byte-exact document (UTF-8, `\n` newlines); `sections` is a flat,
  ordered split on top-level `##` headings (each section includes its own heading
  line; deeper headings stay inside their parent; a non-empty intro before the first
  `##` becomes a leading `{"id": "preamble"}` section; ids are GitHub-style slugs,
  collisions suffixed `-2`, `-3`, … in document order). Concatenating `sections`
  reproduces `content` exactly.
- `REFERENCE_VERSION` policy (mirrors `METADATA_VERSION`): additive changes — a new
  section, appended prose, a new optional field — bump the minor; removing/renaming a
  section `id`, changing the `sections` shape, or dropping/renaming a top-level field
  is breaking and bumps the major. Consumers MUST fail loudly on an unsupported major.
- The export is **engine-global** (base `Transformer` only; no `cls=` parameter) and
  states language facts only.
- Packaging: `transon/resources/LANGUAGE.md` ships in the wheel and sdist;
  `docs/LANGUAGE.md` is the canonical hand-edited source and
  `tests/test_reference.py` asserts the two are identical, pins the section-id list,
  and checks the split parity.
- `python -m transon.reference` prints this JSON.

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
- `tags` is mandatory and must be non-empty. Use `"<rule>"` and/or `"<rule>:<param>"`
  strings (plus `"op:<alternative>"` / `"func:<name>"` for operator/function examples);
  every tag makes the case referenced as an example in the generated docs for that
  entry. Curated cases carry exactly one tier tag (`"worked-example"` or `"recipe"`)
  and nothing else. An untagged case would be unreachable from every reference list —
  the corpus reachability test (`tests/test_docs.py`, `tests/test_metadata.py`) fails
  on it.
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
- Recursion budget: walking one template-nesting level costs one core call-stack frame
  (no `walk`/`_walk`-style per-node doubling), so self-`include`ing templates reach
  depths well past `G_encode` (41) before the host stack overflows; over-depth surfaces
  as the `include` depth-limit `TransformationError`, never a raw `RecursionError`
  (§4 "Recursion budget", Roadmap R-32).

---

## 11. Engine data flow (reference example)

Relocated to the Language Reference: [`docs/LANGUAGE.md`](LANGUAGE.md), "Composition
patterns" (the `zip` + `map` worked end-to-end flow).

---

## 12. Known issues & design questions

Suspected accidental behaviors and open design questions are tracked exclusively in
[`docs/ROADMAP.md`](ROADMAP.md) (`R-xx` items), each with impact analysis,
fix options, and a decision status. This document describes current behavior only.

**Do not "fix" quirky behavior silently** — every behavior change needs an explicit
decision recorded in the roadmap (flip the item's status) and a changelog entry,
since templates in the wild may rely on current behavior.
