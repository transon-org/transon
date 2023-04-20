import pytest

from . import base
from transon import (
    TransformationError,
    Transformer,
)


class FilterDict(base.TableDataBaseCase):
    """
    Iterates over input dict and filters out items with even value.
    """
    tags = ['filter', 'expr']
    template = {
        '$': 'filter',
        'cond': {
            '$': 'expr',
            'op': 'mod',
            'values': [
                {'$': 'value'},
                2,
            ]
        }
    }
    data = {
        'a': 1,
        'b': 2,
        'c': 3,
        'd': 4,
        'e': 5,
        'f': 6,
    }
    result = {
        'a': 1,
        'c': 3,
        'e': 5,
    }


class FilterList(base.TableDataBaseCase):
    """
    Iterates over input list and filters out items with even value.
    """
    tags = ['filter', 'expr']
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
    data = [1, 2, 3, 4, 5, 6]
    result = [1, 3, 5]


def test_invalid_value():
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
