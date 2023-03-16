from transon import Transformer


def test_chain_attr():
    transformer = Transformer({
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
    })

    data = [
        {'a': {'b': {'c': 1}}, 'd': {'e': {'f': 2}}},
        {'a': {'b': {'c': 3}}, 'd': {'e': {'f': 4}}},
    ]

    assert transformer.transform(data) == [
        {'key': 1, 'value': 2},
        {'key': 3, 'value': 4},
    ]
