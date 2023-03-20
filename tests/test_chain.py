from . import base


class ChainWithAttr(base.TableDataBaseCase):
    """
    Searching for values in nested structure with sequence of `attr` operations chained together.
    """
    tags = ['map:item', 'chain']
    template = {
        '$': 'map',
        'item': {
            'key': {
                '$': 'chain',
                'funcs': [
                    {'$': 'item'},
                    {'$': 'attr', 'name': 'a'},
                    {'$': 'attr', 'name': 'b'},
                    {'$': 'attr', 'name': 'c'},
                ],
            },
            'value': {
                '$': 'chain',
                'funcs': [
                    {'$': 'item'},
                    {'$': 'attr', 'name': 'd'},
                    {'$': 'attr', 'name': 'e'},
                    {'$': 'attr', 'name': 'f'},
                ]
            },
        },
    }
    data = [
        {'a': {'b': {'c': 1}}, 'd': {'e': {'f': 2}}},
        {'a': {'b': {'c': 3}}, 'd': {'e': {'f': 4}}},
    ]
    result = [
        {'key': 1, 'value': 2},
        {'key': 3, 'value': 4},
    ]
