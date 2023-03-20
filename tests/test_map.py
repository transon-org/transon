from . import base


class MapListToList(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['chain', 'join', 'map:item', 'item']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'join',
                'items': [
                    {'$': 'attr', 'name': 'first'},
                    {'$': 'attr', 'name': 'second'},
                ]
            },
            {
                '$': 'map',
                'item': {
                    'value': {'$': 'item'}
                }
            }
        ]
    }
    data = {
        'first': [1, 2, 3],
        'second': [4, 5, 6],
    }
    result = [
        {'value': 1},
        {'value': 2},
        {'value': 3},
        {'value': 4},
        {'value': 5},
        {'value': 6},
    ]


class MapDictToList(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['map:item', 'key', 'value']
    template = {
        '$': 'map',
        'item': {
            'key': {'$': 'key'},
            'value': {'$': 'value'},
        }
    }
    data = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
    result = [
        {'key': 'a', 'value': 1},
        {'key': 'b', 'value': 2},
        {'key': 'c', 'value': 3},
    ]


class MapDictToDictItems(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['map:key', 'map:value', 'key', 'value']
    template = {
        '$': 'map',
        'key': {'$': 'value'},
        'value': {'$': 'key'},
    }
    data = {
        'a': 'd',
        'b': 'e',
        'c': 'f',
    }
    result = {
        'd': 'a',
        'e': 'b',
        'f': 'c',
    }


class MapDictToListItems(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['map:items', 'key', 'value']
    template = {
        '$': 'map',
        'items': [
            {'$': 'key'},
            {'$': 'value'},
        ]
    }
    data = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
    result = [
        'a', 1,
        'b', 2,
        'c', 3,
    ]


class MapListsToDict(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['chain', 'zip', 'map:key', 'map:value', 'attr:name']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'zip',
                'items': [
                    {'$': 'attr', 'name': 'keys'},
                    {'$': 'attr', 'name': 'values'},
                ]
            },
            {
                '$': 'map',
                'key': {'$': 'attr', 'name': 0},
                'value': {'$': 'attr', 'name': 1},
            }
        ]
    }
    data = {
        'keys': ['a', 'b', 'c'],
        'values': [1, 2, 3],
    }
    result = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
