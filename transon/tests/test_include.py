from . import base


class Include(base.TableDataBaseCase):
    tags = ['include']
    template = {
        '$': 'map',
        'item': {
            '$': 'include',
            'name': 'MapListsToDict',
        },
    }
    data = [
        {
            'keys': ['a', 'b', 'c'],
            'values': [1, 2, 3],
        },
        {
            'keys': ['d', 'e', 'f'],
            'values': [4, 5, 6],
        },
    ]
    result = [
        {
            'a': 1,
            'b': 2,
            'c': 3,
        },
        {
            'd': 4,
            'e': 5,
            'f': 6,
        }
    ]
