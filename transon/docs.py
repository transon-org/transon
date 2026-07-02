import importlib
import importlib.metadata
import inspect
import pkgutil

from functools import lru_cache
from types import ModuleType
from typing import Union

from transon import Transformer


def import_submodules(package: Union[ModuleType, str], recursive=True):  # pragma: no cover
    if isinstance(package, str):
        try:
            package = importlib.import_module(package)
        except Exception:
            return {}
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        try:
            results[full_name] = importlib.import_module(full_name)
        except Exception:
            pass
        else:
            if recursive and is_pkg:
                results.update(import_submodules(full_name))
    return results


@lru_cache(maxsize=None)
def get_test_cases():
    from transon.tests.base import TableDataBaseCase
    import_submodules('transon.tests')
    return list(TableDataBaseCase.iterate_valid_cases())


@lru_cache(maxsize=None)
def get_error_cases():
    from transon.tests.base import ErrorBaseCase
    import_submodules('transon.tests')
    return list(ErrorBaseCase.iterate_valid_cases())


@lru_cache(maxsize=None)
def get_test_cases_by_tag(tag: str):
    return [
        case
        for case in get_test_cases()
        if tag in case.tags
    ]


@lru_cache(maxsize=None)
def get_test_case_by_name(name: str):
    for case in get_test_cases():
        if case.__name__ == name:
            return case


def template_loader(name: str, context=None):
    case = get_test_case_by_name(name)
    return context.transformer(case.template)


def get_rules_docs(cls=Transformer):
    return [
        {
            'name': rule.__rule_name__,
            'doc': inspect.getdoc(rule),
        }
        for rule in cls.get_rules()
    ]


def get_operators_docs(cls=Transformer):
    return cls.get_operators()


def get_functions_docs(cls=Transformer):
    return cls.get_functions()


def get_rule_parameter_docs(rule_name, cls=Transformer):
    rule = cls.get_rule(rule_name)
    return [
        {
            'name': param_name,
            'doc': inspect.cleandoc(param_docs),
        }
        for param_name, param_docs in rule.__rule_params__.items()
    ]


def serialize_case(case):
    """Serialize one corpus case to the shared example shape.

    ``tags`` is included verbatim — the corpus's own organizing metadata (what a
    case demonstrates, an engine fact) travels with every example, so consumers
    can group/filter without re-deriving anything. No display order, difficulty,
    titles, or other presentation vocabulary is emitted — that is consumer-owned.
    """
    return {
        'name': case.__name__,
        'doc': inspect.getdoc(case),
        'template': case.template,
        'data': case.data,
        'result': case.result,
        'tags': list(case.tags),
    }


def get_example_corpus():
    """The flat example corpus: every valid case serialized **exactly once**.

    This is the single example block both export APIs embed; every other
    ``examples`` field is an ordered list of ``name`` references into it.
    Case names are unique across the corpus (they double as ``include``-able
    template names via :func:`template_loader`), so ``name`` is the join key.
    """
    return [serialize_case(case) for case in get_test_cases()]


def get_example_names_for_tag(tag):
    """Ordered names of the corpus cases carrying ``tag``.

    The tag join is **engine-owned**: consumers resolve these names against
    :func:`get_example_corpus` and never re-derive membership from the tag
    conventions (``"<rule>"``, ``"<rule>:<param>"``, ``"op:<alternative>"``,
    ``"func:<name>"``, tier tags).
    """
    return [case.__name__ for case in get_test_cases_by_tag(tag)]


def get_example_names_for_rule(rule_name):
    return get_example_names_for_tag(rule_name)


def get_example_names_for_rule_param(rule_name, param_name):
    return get_example_names_for_tag(f'{rule_name}:{param_name}')


def get_example_names_for_operator(alternative):
    return get_example_names_for_tag(f'op:{alternative}')


def get_example_names_for_function(name):
    return get_example_names_for_tag(f'func:{name}')


def get_worked_example_names():
    """Names of the curated worked-example tier: end-to-end, real-world-framed cases.

    Convention: curated cases carry **only** their tier tag
    (``['worked-example']``) so they never appear in the per-rule/param
    reference galleries; reference cases never carry a tier tag.
    """
    return get_example_names_for_tag('worked-example')


def get_recipe_names():
    """Names of the curated recipe tier: task-oriented "how do I…" cases.

    Convention: curated cases carry **only** their tier tag (``['recipe']``)
    so they never appear in the per-rule/param reference galleries; reference
    cases never carry a tier tag.
    """
    return get_example_names_for_tag('recipe')


def get_error_examples():
    from transon.tests.base import undefined
    return [
        {
            'name': case.__name__,
            'doc': inspect.getdoc(case),
            'template': case.template,
            'data': None if case.data is undefined else case.data,
            'error': case.error,
            'error_type': case.error_type,
            'action': case.action,
        }
        for case in get_error_cases()
    ]


def get_all_docs(cls=Transformer):
    """The complete docs-site JSON document.

    Examples are **normalized**: the flat ``examples`` block carries every
    corpus case exactly once (:func:`get_example_corpus`), and every other
    ``examples`` field — rule-, parameter-, operator-, and function-level,
    plus the ``worked_examples`` / ``recipes`` tiers — is an ordered list of
    ``name`` references into it. The ``errors`` block stays inline (error
    cases live in a different shape and appear exactly once).
    """
    return {
        'version': importlib.metadata.version('transon'),
        'doc': inspect.getdoc(cls),
        'examples': get_example_corpus(),
        'worked_examples': get_worked_example_names(),
        'recipes': get_recipe_names(),
        'errors': get_error_examples(),
        'rules': [
            {
                'rule': rule_doc,
                'examples': get_example_names_for_rule(rule_doc['name']),
                'params': [
                    {
                        'param': param,
                        'examples': get_example_names_for_rule_param(rule_doc['name'], param['name']),
                    }
                    for param in get_rule_parameter_docs(rule_doc['name'], cls)
                ]
            }
            for rule_doc in get_rules_docs(cls)
        ],
        'operators': [
            {
                'operator': operator_doc,
                'examples': get_example_names_for_operator(operator_doc['alternative']),
            }
            for operator_doc in get_operators_docs()
        ],
        'functions': [
            {
                'function': function_doc,
                'examples': get_example_names_for_function(function_doc['name']),
            }
            for function_doc in get_functions_docs()
        ],
    }


if __name__ == '__main__':  # pragma: no cover
    def main():
        import json
        print(json.dumps(get_all_docs(), indent=4))
        for case in (*get_test_cases(), *get_error_cases()):
            doc = inspect.getdoc(case)
            if 'TBD' in doc:
                print(f'no doc in {case}: {doc}')
        print(len(get_test_cases()))
    main()
