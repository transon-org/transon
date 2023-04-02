from . import base


class MapListToList(base.TableDataBaseCase):
    """
    Maps two lists obtained from different attributes of input.
    Then joins two obtained lists into single resulting list.
    """
    tags = ['chain', 'join', 'map:item', 'item']
    template = {
        '$': 'join',
        'items': [
            {
                '$': 'chain',
                'funcs': [
                    {'$': 'attr', 'name': 'first'},
                    {
                        '$': 'map',
                        'item': {
                            'first': {'$': 'item'}
                        }
                    }
                ]
            },
            {
                '$': 'chain',
                'funcs': [
                    {'$': 'attr', 'name': 'second'},
                    {
                        '$': 'map',
                        'item': {
                            'second': {'$': 'item'}
                        }
                    }
                ]
            },
        ]
    }
    data = {
        'first': [1, 2, 3],
        'second': [4, 5, 6],
    }
    result = [
        {'first': 1},
        {'first': 2},
        {'first': 3},
        {'second': 4},
        {'second': 5},
        {'second': 6},
    ]


class MapDictToList(base.TableDataBaseCase):
    """
    Iterates over input dict and produces list of dicts with corresponding fields for keys and values.
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
    Iterates over input dictionary and produces dictionary with keys and values swapped.
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
    Iterates over input dictionary and produces interlaced list of both keys and values.
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
    Zips two lists containing keys and values together into pairs.
    Then iterates over list of pairs and produces resulting dict.
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
