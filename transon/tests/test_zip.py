from . import base


class ZipLists(base.TableDataBaseCase):
    """
    Transposes parallel lists into rows of paired values.
    Each row is a list (not a Python tuple), so the result is JSON-friendly.
    """
    tags = ['zip', 'zip:items']
    template = {
        '$': 'zip',
        'items': [
            ['a', 'b', 'c'],
            [1, 2, 3],
        ],
    }
    data = None
    result = [
        ['a', 1],
        ['b', 2],
        ['c', 3],
    ]


class ZipStrings(base.TableDataBaseCase):
    """
    Strings are iterables: zipping them pairs characters, like Python's `zip`.
    """
    tags = ['zip']
    template = {
        '$': 'zip',
        'items': ['ab', '12'],
    }
    data = None
    result = [
        ['a', '1'],
        ['b', '2'],
    ]
