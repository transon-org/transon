from transon import Transformer
from transon.docs import (
    get_all_docs,
    get_operators_docs,
    get_functions_docs,
)


def test_docs():
    get_all_docs()


def test_operators_docs_match_registry():
    documented = set()
    for operator in get_operators_docs():
        documented.add(operator['name'])
        documented.add(operator['alternative'])
    assert documented == set(Transformer._operators)


def test_functions_docs_match_registry():
    documented = {function['name'] for function in get_functions_docs()}
    assert documented == set(Transformer._functions)


def test_all_docs_expose_operators_and_functions():
    docs = get_all_docs()
    assert {entry['operator']['name'] for entry in docs['operators']} == {
        operator['name'] for operator in get_operators_docs()
    }
    assert {entry['function']['name'] for entry in docs['functions']} == {
        function['name'] for function in get_functions_docs()
    }
