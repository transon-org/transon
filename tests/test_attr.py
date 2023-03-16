from transon import Transformer


def test_attr_simple():
    transformer = Transformer({
        '$': 'attr',
        'name': 'a',
    })

    data = {
        'a': 1
    }

    assert transformer.transform(data) == 1


def test_attr_reference():
    transformer = Transformer({
        '$': 'attr',
        'name': {
            '$': 'attr',
            'name': 'name'
        },
    })

    data = {
        'a': 1,
        'b': 2,
        'name': 'a',
    }
    assert transformer.transform(data) == 1

    data = {
        'a': 1,
        'b': 2,
        'name': 'b',
    }
    assert transformer.transform(data) == 2


def test_attr_names():
    transformer = Transformer([
        {'$': 'attr', 'names': ['a', 'b', 'c']},
        {'$': 'attr', 'names': ['a', 'b', 'd']},
        {'$': 'attr', 'names': ['a', 'e', 'f']},
        {'$': 'attr', 'names': ['a', 'e', 'g']},
    ])

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
    assert transformer.transform(data) == [1, 2, 3, 4]


def test_attr_dynamic():
    transformer = Transformer({
        '$': 'attr',
        'names': {'$': 'attr', 'name': 'path'},
    })

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
    assert transformer.transform(data) == 3


def test_attr_dynamic_multiple():
    transformer = Transformer({
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
    })

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
    assert transformer.transform(data) == [2, 1, 4, 3]
