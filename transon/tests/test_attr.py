from . import base
from . import base_attr


class AttrSimpleFixedName(base.TableDataBaseCase):
    """
    Gets value from input `dict` by the name of attribute defined in template as constant value.
    """
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': 'a',
    }
    data = {
        'a': 1
    }
    result = 1


class AttrSimpleNameDoesNotExist(base.TableDataBaseCase):
    """
    Attempts to get a value from input `dict` by the name that does not exist.
    """
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': 'b',
    }
    data = {
        'a': 1
    }
    result = None


class AttrSimplePathDoesNotExist1(base.TableDataBaseCase):
    """
    Tries to get a value from nested input structure of `dicts` with paths defined in different attribute of input data.
    Actual path is not correct at its second component.
    Template results with no value.
    """
    tags = []
    template = {
        '$': 'attr',
        'names': ['a', 'x', 'c'],
    }
    data = {
        'a': {
            'b': {
                'c': 1
            }
        }
    }
    result = None


class AttrSimplePathDoesNotExist2(base.TableDataBaseCase):
    """
    Tries to get a value from nested input structure of `lists` with paths defined in different attribute of input data.
    Actual path is not correct at its second component.
    Template results with no value.
    """
    tags = []
    template = {
        '$': 'attr',
        'names': [0, 1, 0],
    }
    data = [[[1]]]
    result = None


class AttrSimpleFixedIndex(base.TableDataBaseCase):
    """
    Gets value from input `list` by the index defined in template as constant value.
    """
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': 0,
    }
    data = [1]
    result = 1


class AttrSimpleIndexDoesNotExist(base.TableDataBaseCase):
    """
    Attempts to get a value from input `list` by the index that does not exist.
    """
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': 2,
    }
    data = [1]
    result = None


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


class AttrSimpleFixedNames(base.TableDataBaseCase):
    """
    Gets a `list` of values with 4 elements discovered in nested input structure of `dicts` with paths defined in template.
    """
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


class AttrDynamicReferenceNames(base.TableDataBaseCase):
    """
    Gets value from nested input structure of `dicts` with paths defined in different attribute of input data.
    """
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


class AttrDynamicReferenceMultipleNames(base.TableDataBaseCase):
    """
    Gets a `list` of values discovered in nested input structure of `dicts` with paths defined in input data.
    List of paths may include any number of paths of any depth.
    """
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
