import pytest

from transon import (
    Transformer,
    TransformationError,
)


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
