from transon import Transformer


def test_map_join():
    transformer = Transformer({
        '$': 'chain',
        'funcs': [
            {
                '$': 'join',
                'items': [
                    {'$': 'attr', 'name': 'first'},
                    {'$': 'attr', 'name': 'second'},
                ]
            },
            {
                '$': 'map',
                'item': {
                    'value': {'$': 'this'}
                }
            }
        ]
    })
    assert transformer.transform({
        'first': [1, 2, 3],
        'second': [4, 5, 6],
    }) == [
        {'value': 1},
        {'value': 2},
        {'value': 3},
        {'value': 4},
        {'value': 5},
        {'value': 6},
    ]


def test_map_item():
    transformer = Transformer({
        '$': 'map',
        'item': {
            'key': {'$': 'key'},
            'value': {'$': 'value'},
        }
    })

    assert transformer.transform({
        'a': 1,
        'b': 2,
        'c': 3,
    }) == [
        {'key': 'a', 'value': 1},
        {'key': 'b', 'value': 2},
        {'key': 'c', 'value': 3},
    ]


def test_map_items():
    transformer = Transformer({
        '$': 'map',
        'items': [
            {'$': 'key'},
            {'$': 'value'},
        ]
    })

    assert transformer.transform({
        'a': 1,
        'b': 2,
        'c': 3,
    }) == [
        'a', 1,
        'b', 2,
        'c', 3,
    ]
