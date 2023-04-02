from . import base


class JoinWithStaticBase(base.TableDataBaseCase):
    """
    Enriches input dict with default value.
    """
    tags = ['join', 'this']
    template = {
        '$': 'join',
        'items': [
            {
                'a': 'default',
            },
            {
                '$': 'this',
            },
        ]
    }


class JoinTwoBase(base.TableDataBaseCase):
    """
    Joins two dicts taken from separate attributes of input into one dict.
    """
    tags = ['join']
    template = {
        '$': 'join',
        'items': [
            {
                '$': 'attr',
                'name': 'first',
            },
            {
                '$': 'attr',
                'name': 'second',
            },
        ]
    }
