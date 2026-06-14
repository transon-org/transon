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


def template_loader(name: str):
    case = get_test_case_by_name(name)
    return Transformer(
        case.template,
        template_loader=template_loader,
    )


OPERATOR_DOCS = [
    ('<',  'lt',  'binary', 'any',            'boolean',
     'Less-than comparison: `true` when the left operand is strictly less than the right.'),
    ('<=', 'le',  'binary', 'any',            'boolean',
     'Less-than-or-equal comparison.'),
    ('==', 'eq',  'binary', 'any',            'boolean',
     'Equality comparison: `true` when both operands are equal.'),
    ('!=', 'ne',  'binary', 'any',            'boolean',
     'Inequality comparison: `true` when the operands differ.'),
    ('>=', 'ge',  'binary', 'any',            'boolean',
     'Greater-than-or-equal comparison.'),
    ('>',  'gt',  'binary', 'any',            'boolean',
     'Greater-than comparison.'),
    ('+',  'add', 'binary', 'string, number', 'string, number',
     'Addition for numbers, concatenation for strings.'),
    ('-',  'sub', 'binary', 'number',         'number',
     'Subtraction.'),
    ('*',  'mul', 'binary', 'number',         'number',
     'Multiplication.'),
    ('/',  'div', 'binary', 'number',         'number',
     'True division; the result is a float.'),
    ('%',  'mod', 'binary', 'number',         'number',
     'Modulo: the remainder of a division.'),
    ('&&', 'and', 'binary', 'any',            'any',
     'Logical conjunction by truthiness (Python `and`). Returns one of the operands, '
     'not a strict boolean.'),
    ('||', 'or',  'binary', 'any',            'any',
     'Logical disjunction by truthiness (Python `or`). Returns the first truthy '
     'operand and treats `NO_CONTENT` as falsy.'),
    ('!',  'not', 'unary',  'boolean',        'boolean',
     'Logical negation (Python `not`).'),
]


FUNCTION_DOCS = [
    ('str',   'any', 'str',
     'Convert any value to its string representation (Python `str`).'),
    ('int',   'str', 'int',
     'Parse a string (or number) into an integer (Python `int`). An optional base can '
     'be passed as a second value.'),
    ('float', 'str', 'float',
     'Parse a string (or number) into a floating-point number (Python `float`).'),
]


def get_rules_docs(cls=Transformer):
    return [
        {
            'name': rule.__rule_name__,
            'doc': inspect.getdoc(rule),
        }
        for rule in cls.get_rules()
    ]


def get_operators_docs():
    return [
        {
            'name': name,
            'alternative': alternative,
            'kind': kind,
            'types': types,
            'result': result,
            'doc': doc,
        }
        for name, alternative, kind, types, result, doc in OPERATOR_DOCS
    ]


def get_functions_docs():
    return [
        {
            'name': name,
            'input': input_type,
            'output': output_type,
            'doc': doc,
        }
        for name, input_type, output_type, doc in FUNCTION_DOCS
    ]


def get_rule_parameter_docs(rule_name, cls=Transformer):
    rule = cls.get_rule(rule_name)
    return [
        {
            'name': param_name,
            'doc': inspect.cleandoc(param_docs),
        }
        for param_name, param_docs in rule.__rule_params__.items()
    ]


def get_test_cases_for_tag(tag):
    return [
        {
            'name': case.__name__,
            'doc': inspect.getdoc(case),
            'template': case.template,
            'data': case.data,
            'result': case.result,
        }
        for case in get_test_cases_by_tag(tag)
    ]


def get_test_cases_for_rule(rule_name):
    return get_test_cases_for_tag(rule_name)


def get_test_cases_for_rule_param(rule_name, param_name):
    return get_test_cases_for_tag(f'{rule_name}:{param_name}')


def get_test_cases_for_operator(alternative):
    return get_test_cases_for_tag(f'op:{alternative}')


def get_test_cases_for_function(name):
    return get_test_cases_for_tag(f'func:{name}')


def get_worked_examples():
    return get_test_cases_for_tag('worked-example')


def get_recipes():
    return get_test_cases_for_tag('recipe')


def get_all_docs(cls=Transformer):
    return {
        'version': importlib.metadata.version('transon'),
        'doc': inspect.getdoc(cls),
        'worked_examples': get_worked_examples(),
        'recipes': get_recipes(),
        'rules': [
            {
                'rule': rule_doc,
                'examples': [
                    case
                    for case in get_test_cases_for_rule(rule_doc['name'])
                ],
                'params': [
                    {
                        'param': param,
                        'examples': [
                            case
                            for case in get_test_cases_for_rule_param(rule_doc['name'], param['name'])
                        ]
                    }
                    for param in get_rule_parameter_docs(rule_doc['name'], cls)
                ]
            }
            for rule_doc in get_rules_docs(cls)
        ],
        'operators': [
            {
                'operator': operator_doc,
                'examples': get_test_cases_for_operator(operator_doc['alternative']),
            }
            for operator_doc in get_operators_docs()
        ],
        'functions': [
            {
                'function': function_doc,
                'examples': get_test_cases_for_function(function_doc['name']),
            }
            for function_doc in get_functions_docs()
        ],
    }


if __name__ == '__main__':  # pragma: no cover
    def main():
        import json
        print(json.dumps(get_all_docs(), indent=4))
        for case in get_test_cases():
            doc = inspect.getdoc(case)
            if 'TBD' in doc:
                print(f'no doc in {case}: {doc}')
        print(len(get_test_cases()))
    main()
