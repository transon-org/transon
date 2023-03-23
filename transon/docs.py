import os.path
from collections import defaultdict
import inspect

import unittest
from functools import lru_cache

import transon
from transon.tests.base import TableDataBaseCase
from transon.transformers import Transformer


@lru_cache(maxsize=None)
def get_test_cases_by_tags():
    project_root = os.path.dirname(os.path.dirname(transon.__file__))
    unittest.defaultTestLoader.discover(project_root)

    tests_by_tag = defaultdict(list)
    for case in TableDataBaseCase.iterate_valid_cases():
        for tag in case.tags:
            tests_by_tag[tag].append(case)
    return tests_by_tag


def get_rules_docs(cls=Transformer):
    return [
        {
            'name': rule.__rule_name__,
            'doc': inspect.getdoc(rule),
        }
        for rule in cls.get_rules()
    ]


def get_rule_parameter_docs(rule_name, cls=Transformer):
    rule = cls.get_rule(rule_name)
    return [
        {
            'name': param_name,
            'doc': param_docs,
        }
        for param_name, param_docs in rule.__rule_params__.items()
    ]


def get_test_cases_for_rule(rule_name):
    tests_by_tag = get_test_cases_by_tags()
    return [
        {
            'name': case.__name__,
            'doc': inspect.getdoc(case),
            'template': case.template,
            'data': case.data,
            'result': case.result,
        }
        for case in tests_by_tag[rule_name]
    ]


def get_test_cases_for_rule_param(rule_name, param_name):
    tests_by_tag = get_test_cases_by_tags()
    tag = f'{rule_name}:{param_name}'
    return [
        {
            'name': case.__name__,
            'doc': inspect.getdoc(case),
            'template': case.template,
            'data': case.data,
            'result': case.result,
        }
        for case in tests_by_tag[tag]
    ]


def get_all_docs(cls=Transformer):
    return {
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
        ]
    }


if __name__ == '__main__':  # pragma: no cover
    import json
    print(json.dumps(get_all_docs(), indent=4))
