from . import base


class FilterDict(base.TableDataBaseCase):
    """
    Iterates over input `dict` and filters out items with even value.
    """
    tags = ['filter', 'expr', 'value']
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
    Iterates over input `list` and filters out items with even value.
    """
    tags = ['filter', 'expr', 'item']
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


class FilterListByOddIndex(base.TableDataBaseCase):
    """
    Filters a list, keeping only elements at odd indices (1, 3, 5, ...).
    Demonstrates that ``index`` works inside ``filter`` as well as ``map``.
    """
    tags = ['filter', 'filter:cond', 'index', 'expr']
    template = {
        '$': 'filter',
        'cond': {
            '$': 'expr',
            'op': 'mod',
            'values': [
                {'$': 'index'},
                2,
            ]
        }
    }
    data = ['a', 'b', 'c', 'd', 'e']
    result = ['b', 'd']


class FilterListNoContent(base.TableDataBaseCase):
    """
    Sets some names to context, one with `true` value and one with `false`.
    Iterates over input `list` of string and filters out items with name that is not set to `true` in the context.
    """
    tags = ['chain', 'filter', 'set', 'get']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'set', 'name': 'current'},
            True,
            {'$': 'set', 'name': 'a'},
            False,
            {'$': 'set', 'name': 'b'},
            {'$': 'get', 'name': 'current'},
            {
                '$': 'filter',
                'cond': {
                    '$': 'get',
                    'name': {'$': 'item'},
                }
            }
        ]
    }
    data = ['a', 'b', 'c']
    result = ['a']
