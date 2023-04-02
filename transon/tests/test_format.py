from . import base


class FormatFromSingleValue(base.TableDataBaseCase):
    """
    Iterates list with floats and produces list of strings by formatting each item.
    """
    tags = ['map:item', 'format']
    template = {
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{:.03f}'
        }
    }
    data = [1 / i for i in range(2, 10)]
    result = ['0.500', '0.333', '0.250', '0.200', '0.167', '0.143', '0.125', '0.111']


class FormatFromDict(base.TableDataBaseCase):
    """
    Iterates over list of dicts and produces list of string using items for filling pattern slots.
    """
    tags = ['map:item', 'format']
    template = {
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{name}-{index}'
        }
    }
    data = [
        {'name': 'a', 'index': 1},
        {'name': 'b', 'index': 2},
        {'name': 'c', 'index': 3},
    ]
    result = ['a-1', 'b-2', 'c-3']


class FormatFromList(base.TableDataBaseCase):
    """
    Iterates over list of lists and produces list of string using items for filling pattern slots.
    """
    tags = ['map:item', 'format']
    template = {
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{0}-{1}'
        }
    }
    data = [
        ['a', 1],
        ['b', 2],
        ['c', 3],
    ]
    result = ['a-1', 'b-2', 'c-3']


class FormatWithValue(base.TableDataBaseCase):
    """
    Iterates over list of values.
    For formatting value creates dict with dynamically calculated values.
    Produces list of strings using formatting.
    """
    tags = ['map:item', 'format:value', 'index', 'expr:values']
    template = {
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{x}-{y}',
            'value': {
                'x': {'$': 'this'},
                'y': {
                    '$': 'expr',
                    'op': '+',
                    'values': [{'$': 'index'}, 1]
                }
            }
        }
    }
    data = ['a', 'b', 'c']
    result = ['a-1', 'b-2', 'c-3']
