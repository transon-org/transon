from . import base


class JoinWithStaticBase(base.BaseCase):
    tags = ['join']
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


class JoinTwoBase(base.BaseCase):
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
