from . import base


class JoinWithStaticBase(base.TableDataBaseCase):
    """
    TODO: Describe
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
    TODO: Describe
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
