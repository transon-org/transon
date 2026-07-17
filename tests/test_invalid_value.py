import pytest

from transon import (
    Transformer,
    TransformationError,
)


def test_map_invalid_value():
    template = {
        '$': 'map',
        'item': {'$': 'item'},
    }
    transformer = Transformer(template)
    with pytest.raises(TransformationError):
        transformer.transform(1)


def test_filter_invalid_value():
    template = {
        '$': 'filter',
        'cond': {
            '$': 'expr',
            'op': 'mod',
            'values': [
                {'$': 'item'},
                2,
            ]
        }
    }
    transformer = Transformer(template)
    with pytest.raises(TransformationError):
        transformer.transform(1)


def test_map_items_non_list_result():
    from transon import DefinitionError
    template = {
        '$': 'map',
        'items': {'$': 'this'},
    }
    transformer = Transformer(template)
    with pytest.raises(DefinitionError, match='`items` must evaluate to a list'):
        transformer.transform([{'a': 1}])
