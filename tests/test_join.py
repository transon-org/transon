import pytest

from transon import (
    Transformer,
    TransformationError,
)


def test_join_static_dict(subtests):
    transformer = Transformer({
        '$': 'join',
        'items': [
            {
                'a': 'default',
            },
            {
                '$': 'this',
            },
        ]
    })

    with subtests.test("no override"):
        assert transformer.transform({
            'a': 'b',
            'c': 'd',
        }) == {
            'a': 'b',
            'c': 'd',
        }

    with subtests.test("with override"):
        assert transformer.transform({
            'c': 'd',
            'e': 'f',
        }) == {
            'a': 'default',
            'c': 'd',
            'e': 'f',
        }


def test_join_two_dicts(subtests):
    transformer = Transformer({
        '$': 'join',
        'items': [
            {
                '$': 'attr',
                'name': 'first',
            },
            {
                '$': 'attr',
                'name': 'second',
            },
        ]
    })

    with subtests.test("no common keys"):
        assert transformer.transform({
            'first': {
                'a': 1,
                'b': 2,
            },
            'second': {
                'c': 3,
                'd': 4,
            },
        }) == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
        }

    with subtests.test("with common keys"):
        assert transformer.transform({
            'first': {
                'a': 1,
                'b': 2,
                'c': 5,
            },
            'second': {
                'c': 3,
                'd': 4,
            },
        }) == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
        }

    with subtests.test("with common keys"):
        assert transformer.transform({
            'first': 'hello ',
            'second': 'world!',
        }) == 'hello world!'


def test_join_many_dynamic_dicts(subtests):
    transformer = Transformer({
        '$': 'join',
        'items': {
            '$': 'join',
            'items': [
                {
                    '$': 'map',
                    'item': {
                        '$': 'object',
                        'key': {
                            '$': 'attr',
                            'name': 'key',
                        },
                        'value': {
                            '$': 'attr',
                            'name': 'value',
                        },
                    },
                },
                {
                    '$': 'map',
                    'item': {
                        '$': 'object',
                        'key': {
                            '$': 'attr',
                            'name': 'value',
                        },
                        'value': {
                            '$': 'attr',
                            'name': 'key',
                        },
                    },
                },
            ],
        },
    })
    assert transformer.transform([
        {'key': 'a', 'value': 'b'},
        {'key': 'c', 'value': 'd'},
    ]) == {
        'a': 'b',
        'b': 'a',
        'c': 'd',
        'd': 'c',
    }


def test_join_error():
    transformer = Transformer({
        '$': 'join',
        'items': [
            {'$': 'attr', 'name': 'dict'},
            {'$': 'attr', 'name': 'list'},
        ]
    })
    with pytest.raises(TransformationError):
        transformer.transform({
            'dict': {'a': 1},
            'list': ['b', 2],
        })
