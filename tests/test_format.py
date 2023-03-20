from . import base


class FormatFromSingleValue(base.TableDataBaseCase):
    """
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
    """
    tags = ['map:item', 'format:value', 'index']
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
