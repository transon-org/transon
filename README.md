# transon

![PyPI](https://img.shields.io/pypi/v/transon)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/transon)
![Codecov](https://img.shields.io/codecov/c/github/transon-org/transon)
![PyPI - Downloads](https://img.shields.io/pypi/dm/transon)

> Homogeneous JSON template engine — the template is itself plain JSON.

## What is transon?

`transon` reshapes one JSON document into another using a template that is itself plain
JSON. Instead of writing imperative glue code to walk and rebuild data, you describe the
*shape* of the output once and let the engine fill it in from the input — there is no
separate template language and no string-embedded DSL to learn.

```
                    ┌─────────────────┐
                    │  JSON Template  │
                    └────────┬────────┘
                             │
┌──────────────┐    ┌────────▼────────┐    ┌───────────────┐
│  JSON Input  ├────►     transon     ├────►  JSON Output  │
└──────────────┘    └─────────────────┘    └───────────────┘
```

It is **inspired by** [XSLT](https://en.wikipedia.org/wiki/XSLT) (declarative,
tree-to-tree transformation) and [JsonLogic](https://jsonlogic.com/) (logic expressed as
data), applying those ideas to JSON-to-JSON transformation.

Documentation and playground: https://transon-org.github.io/

## What you can do

Beyond simple interpolation, `transon` offers:

- **Static validation** — `Transformer(template, validate=True)` (or calling
  `.validate()`) checks the template's structure up front, without any input data.
- **Defaults for missing values** — `attr`, `get`, `join`, `format`, and `include`
  accept a `default` template, used when the looked-up value is absent.
- **A "no value" model** — missing data produces the `NO_CONTENT` sentinel; container
  rules skip it instead of emitting `null`, so optional data simply disappears from the
  output.
- **Literal keys** — the `object` rule's `fields` mode builds dicts with literal keys,
  including a key equal to the marker (`$`).
- **Configurable marker** — `Transformer(template, marker="@")` if `$` collides with
  your data.
- **Safe output** — `transform(data, copy_output=True)` deep-copies the result so it
  shares no mutable structure with the input (which is never mutated regardless).
- **A clear error model** — `DefinitionError` for malformed templates,
  `TransformationError` for data that does not fit; messages include the template path
  where the problem occurred (`at template → …`).
- **I/O delegates** — the `file` rule writes through a `file_writer` callback and the
  `include` rule loads sub-templates through a `template_loader` callback.
- **Offline docs & metadata exports** — the installed package serves its own
  [Language Reference](transon/resources/LANGUAGE.md)
  (`transon.reference.get_language_reference()`), editor metadata, and generated docs.

## Development Principles

`transon` was built with a set of key development principles in mind, including:

 - **Flexibility and Extensibility**: `transon` is designed to be highly flexible and extensible, allowing you to add new rules and types of placeholders to suit your unique needs.
 - **Valid JSON Structure**: `transon` templates are defined as valid JSON structures, making them easy to work with and compatible with a wide range of tools and applications.
 - **Composable Rules**: `transon` rules are highly composable, allowing you to define complex behavior patterns using a combination of nested rules. 
For example, arithmetic expressions can be defined with nested rules, where each rule represents a specific operation. 
This approach eliminates the need for a domain-specific language (DSL) for arithmetic expressions.
 - **Marker-Based Templates**: The most important aspect of a `transon` template is the use of the `$` marker. 
This marker is a special key within the JSON structure that distinguishes it from other types of JSON data. 
By default, the `$` key is used as the marker, but you can change it to any other value you prefer.
 
By using a marker-based approach, `transon` ensures that templates are easy to work with and can be easily distinguished from other types of JSON data. 
This makes it simple to generate dynamic templates, manipulate JSON data, and produce new JSON structures that meet your specific requirements. 
Additionally, the composable rules approach allows for advanced behavior patterns that can be defined using a combination of nested rules, making `transon` highly flexible and extensible.

## Installation
`transon` can be installed using pip, the Python package manager. 
Simply run the following command:

```shell
pip install transon
```

## Development

Requires Python 3.9+ and [uv](https://docs.astral.sh/uv/).

```shell
uv sync --dev
uv run pytest .
```

## Comparison

JSON transformation is a crowded space. `transon`'s bet is that **templates are
themselves pure JSON** — storable, generatable, diff-able, and extensible with your own
rules — traded against the terseness of a string DSL. Pick the tool that fits the job:

| Tool | Template / language | Extensible | Deps & runtime | Best when |
|---|---|---|---|---|
| **transon** | pure JSON tree | custom rules, operators, functions | none (Python stdlib) | templates must be stored / generated / validated as JSON, with domain-specific rules, in Python |
| [JSONata](https://jsonata.org/) | string expression DSL | limited | JS library | concise queries & expressions over JSON in JavaScript |
| [jq](https://jqlang.github.io/jq/) | string filter language | limited | native binary | CLI piping and ad-hoc filtering in the shell |
| [JSLT](https://github.com/schibsted/jslt) | string DSL (jq-like) | user functions | JVM | compact JSON→JSON on the JVM |
| [Jolt](https://github.com/bazaarvoice/jolt) | JSON spec | limited | JVM | declarative structural reshaping on the JVM |
| [JsonLogic](https://jsonlogic.com/) | JSON logic tree | limited | small libs (many languages) | portable business/boolean rules shared across services |
| [JSON-e](https://json-e.js.org/) | JSON template | limited | JS / Python | parameterising JSON config with interpolation |
| [Jsonnet](https://jsonnet.org/) | full templating language | yes | native binary | generating large config (e.g. Kubernetes) from a real language |
| [json-templates](https://github.com/datavis-tech/json-templates) | JSON with `{{placeholders}}` | no | tiny JS library | simple value substitution into a JSON skeleton |


**Where `transon` is _not_ the best pick** (worth being honest about):

- **Expression-heavy** transforms read far more concisely in a string DSL like JSONata
  or jq — `transon` spells `(a + b) * c` as a nested rule tree.
- **Maturity & ecosystem**: jq and JSONata are battle-tested with large communities;
  `transon` is young and Python-only.

### The trade-off, concretely

The same transform — *multiply each order's `qty` by its `price`* — over input
`{"orders": [{"qty": 2, "price": 3}, {"qty": 5, "price": 7}]}`:

JSONata — a terse string expression:

```
orders.(qty * price)
```

`transon` — pure JSON, composable rules:

```json
{
  "$": "chain",
  "funcs": [
    {"$": "attr", "name": "orders"},
    {
      "$": "map",
      "item": {
        "$": "expr",
        "op": "mul",
        "values": [
          {"$": "attr", "name": "qty"},
          {"$": "attr", "name": "price"}
        ]
      }
    }
  ]
}
```

Both yield `[6, 35]`. JSONata wins on brevity; `transon` wins when the template itself
must be **data** — stored in a database, generated by another program, reviewed as a
diff, checked with `Transformer.validate()`, or extended with your own rules.
