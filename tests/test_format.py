from transon import Transformer


def test_with_single_value():
    transformer = Transformer({
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{:.03f}'
        }
    })

    assert transformer.transform([
        1 / i for i in range(2, 10)
    ]) == ['0.500', '0.333', '0.250', '0.200', '0.167', '0.143', '0.125', '0.111']


def test_with_dict():
    transformer = Transformer({
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{name}-{index}'
        }
    })

    assert transformer.transform([
        {'name': 'a', 'index': 1},
        {'name': 'b', 'index': 2},
        {'name': 'c', 'index': 3},
    ]) == ['a-1', 'b-2', 'c-3']


def test_with_list():
    transformer = Transformer({
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{0}-{1}'
        }
    })

    assert transformer.transform([
        ['a', 1],
        ['b', 2],
        ['c', 3],
    ]) == ['a-1', 'b-2', 'c-3']


def test_with_value():
    transformer = Transformer({
        '$': 'map',
        'item': {
            '$': 'format',
            'pattern': '{x}-{y}',
            'value': {
                'x': {'$': 'this'},
                'y': {
                    '$': 'expr',
                    'op': '+',
                    'values': [{'$': 'index'}, 1]
                }
            }
        }
    })

    assert transformer.transform([
        'a',
        'b',
        'c',
    ]) == ['a-1', 'b-2', 'c-3']
