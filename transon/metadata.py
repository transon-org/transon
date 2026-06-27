"""Projection-ready editor-metadata export.

A dedicated, versioned export — separate from the docs API — that emits the shape
the ``transon-blockly`` visual editor consumes (see that repo's
``docs/metadata-contract.md`` §2). The payload is **split** into a lean structural
*catalog* (consumed by the editor's generators) and an *examples/docs* payload
(tooltips/examples), joined by ``name``.

The export states **engine facts only**: pre-derived variant signatures, per-param
``kind`` (dynamic vs constant), and resolved enum domains (``options``). No Blockly
shapes, colours, or widget choices — those live in the editor's projection.
"""
import importlib.metadata
import inspect

from transon import Transformer
from transon import Domain
from transon import docs

METADATA_VERSION = '2.0'


def _operator_options(cls=Transformer):
    options = []
    for entry in cls.get_operators():
        for token in (entry.get('name'), entry.get('alternative')):
            if token is not None and token not in options:
                options.append(token)
    return options


def _function_options(cls=Transformer):
    return [entry['name'] for entry in cls.get_functions()]


def _resolve_options(domain, cls):
    if domain is Domain.OPERATOR:
        return _operator_options(cls)
    return _function_options(cls)


def derive_variants(rule):
    """Build editor variant signatures from a rule's declared ``variants`` schema.

    Each declared variant is a complete required-parameter shape; this attaches the
    rule's optional parameters (flagged ``required: false``) and the discriminating
    ``id`` (the variant minus the params shared by every variant). Consumers read
    these directly and never re-derive the set algebra.
    """
    schema = getattr(rule, '__rule_schema__', {})
    params = list(getattr(rule, '__rule_params__', {}))
    variant_sets = list(schema.get('variants', (frozenset(),)))
    required = frozenset.intersection(*variant_sets)
    optional = [
        name for name in params
        if all(name not in variant_set for variant_set in variant_sets)
    ]

    signatures = []
    for variant_set in variant_sets:
        mode = [name for name in params if name in (variant_set - required)]
        entry_params = []
        for name in params:
            if name in variant_set:
                entry_params.append({'name': name, 'required': True})
            elif name in optional:
                entry_params.append({'name': name, 'required': False})
        signatures.append({
            'id': '+'.join(mode) if mode else 'base',
            'params': entry_params,
        })
    return signatures


def _catalog_params(rule, cls):
    specs = getattr(rule, '__rule_param_meta__', {})
    params = []
    for name, spec in specs.items():
        entry = {'name': name, 'kind': spec.kind.value}
        if spec.domain is not None:
            entry['options'] = _resolve_options(spec.domain, cls)
        params.append(entry)
    return params


def _catalog_rule(rule, cls):
    return {
        'name': rule.__rule_name__,
        'params': _catalog_params(rule, cls),
        'variants': derive_variants(rule),
    }


def _catalog_operator(entry):
    return {
        key: entry.get(key)
        for key in ('name', 'alternative', 'kind', 'types', 'result')
    }


def _catalog_function(entry):
    return {key: entry.get(key) for key in ('name', 'input', 'output')}


def _docs_rule(rule, cls):
    name = rule.__rule_name__
    return {
        'name': name,
        'description': inspect.getdoc(rule),
        'params': [
            {
                'name': param['name'],
                'description': param['doc'],
                'examples': docs.get_test_cases_for_rule_param(
                    name, param['name']
                ),
            }
            for param in docs.get_rule_parameter_docs(name, cls)
        ],
        'examples': docs.get_test_cases_for_rule(name),
    }


def _docs_operator(entry):
    return {
        'name': entry['name'],
        'doc': entry.get('doc'),
        'examples': docs.get_test_cases_for_operator(entry.get('alternative')),
    }


def _docs_function(entry):
    return {
        'name': entry['name'],
        'doc': entry.get('doc'),
        'examples': docs.get_test_cases_for_function(entry['name']),
    }


def get_editor_metadata(cls=Transformer):
    """Return the projection-ready editor metadata for ``cls`` (default ``Transformer``).

    The result has a standalone ``metadata_version``, the ``engine_version``, and a
    split ``catalog`` (structural) / ``docs`` (examples) payload joined by ``name``.
    """
    rules = cls.get_rules()
    operators = cls.get_operators()
    functions = cls.get_functions()
    return {
        'metadata_version': METADATA_VERSION,
        'engine_version': importlib.metadata.version('transon'),
        'catalog': {
            'rules': [_catalog_rule(rule, cls) for rule in rules],
            'operators': [_catalog_operator(entry) for entry in operators],
            'functions': [_catalog_function(entry) for entry in functions],
        },
        'docs': {
            'rules': [_docs_rule(rule, cls) for rule in rules],
            'operators': [_docs_operator(entry) for entry in operators],
            'functions': [_docs_function(entry) for entry in functions],
        },
    }


if __name__ == '__main__':  # pragma: no cover
    import json
    print(json.dumps(get_editor_metadata(), indent=4))
