from . import base
from . import base_attr


class AttrSimpleFixedName(base.BaseCase):
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': 'a',
    }
    data = {
        'a': 1
    }
    result = 1


class AttrDynamicReferenceName1(base_attr.AttrDynamicReferenceName):
    data = {
        'a': 1,
        'b': 2,
        'name': 'a',
    }
    result = 1


class AttrDynamicReferenceName2(base_attr.AttrDynamicReferenceName):
    data = {
        'a': 1,
        'b': 2,
        'name': 'b',
    }
    result = 2


class AttrSimpleFixedNames(base.BaseCase):
    tags = ['attr:names']
    template = [
        {'$': 'attr', 'names': ['a', 'b', 'c']},
        {'$': 'attr', 'names': ['a', 'b', 'd']},
        {'$': 'attr', 'names': ['a', 'e', 'f']},
        {'$': 'attr', 'names': ['a', 'e', 'g']},
    ]
    data = {
        'a': {
            'b': {
                'c': 1,
                'd': 2,
            },
            'e': {
                'f': 3,
                'g': 4,
            }
        },
    }
    result = [1, 2, 3, 4]


class AttrDynamicReferenceNames(base.BaseCase):
    tags = ['attr:names']
    template = {
        '$': 'attr',
        'names': {'$': 'attr', 'name': 'path'},
    }
    data = {
        'a': {
            'b': {
                'c': 1,
                'd': 2,
            },
            'e': {
                'f': 3,
                'g': 4,
            }
        },
        'path': ['a', 'e', 'f']
    }
    result = 3


class AttrDynamicReferenceMultipleNames(base.BaseCase):
    tags = ['attr:names', 'chain', 'set', 'get', 'map:item']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'set', 'name': 'root'},
            {'$': 'attr', 'name': 'paths'},
            {
                '$': 'map',
                'item': {
                    '$': 'chain',
                    'funcs': [
                        {'$': 'get', 'name': 'root'},
                        {
                            '$': 'attr',
                            'names': {'$': 'item'}
                        }
                    ],
                }
            }
        ],
    }
    data = {
        'a': {
            'b': {'c': 1, 'd': 2},
            'e': {'f': 3, 'g': 4}
        },
        'paths': [
            ['a', 'b', 'd'],
            ['a', 'b', 'c'],
            ['a', 'e', 'g'],
            ['a', 'e', 'f'],
        ]
    }
    result = [2, 1, 4, 3]
