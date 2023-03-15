from transon import Transformer


def test_sum_squares():
    transformer = Transformer({
        '$': 'chain',
        'funcs': [
            {
                '$': 'chain',
                'funcs': [
                    {'$': 'attr', 'name': 'a'},
                    {
                        '$': 'expr',
                        'op': '*',
                        'value': {'$': 'this'},
                    }
                ]
            },
            {
                '$': 'expr',
                'op': '+',
                'value': {
                    '$': 'chain',
                    'funcs': [
                        {'$': 'parent'},
                        {'$': 'attr', 'name': 'b'},
                        {
                            '$': 'expr',
                            'op': '*',
                            'value': {'$': 'this'},
                        }
                    ]
                },
            }
        ]
    })

    data = {
        'a': 3,
        'b': 4,
    }

    assert transformer.transform(data) == 25


def test_add_string_suffix():
    transformer = Transformer({
        '$': 'expr',
        'op': '+',
        'value': '_suffix',
    })

    assert transformer.transform('value') == 'value_suffix'


def test_value_add_string_prefix():
    transformer = Transformer({
        '$': 'chain',
        'funcs': [
            "prefix_",
            {
                '$': 'expr',
                'op': '+',
                'value': {'$': 'parent'},
            }
        ]
    })

    assert transformer.transform('value') == 'prefix_value'


def test_values_sum_squares():
    transformer = Transformer({
        '$': 'expr',
        'op': '+',
        'values': [
            {
                '$': 'expr',
                'op': '*',
                'values': [
                    {'$': 'attr', 'name': 'a'},
                    {'$': 'attr', 'name': 'a'},
                ]
            },
            {
                '$': 'expr',
                'op': '*',
                'values': [
                    {'$': 'attr', 'name': 'b'},
                    {'$': 'attr', 'name': 'b'},
                ]
            },
        ]
    })

    data = {
        'a': 3,
        'b': 4,
    }

    assert transformer.transform(data) == 25


def test_values_add_string_suffix():
    transformer = Transformer({
        '$': 'expr',
        'op': '+',
        'values': [
            {'$': 'this'},
            '_suffix',
        ]
    })

    assert transformer.transform('value') == 'value_suffix'


def test_values_add_string_prefix():
    transformer = Transformer({
        '$': 'expr',
        'op': '+',
        'values': [
            "prefix_",
            {'$': 'this'},
        ]
    })

    assert transformer.transform('value') == 'prefix_value'


def test_unary_operator(subtests):
    with subtests.test("!"):
        transformer = Transformer({
            '$': 'expr',
            'op': '!',
        })

        assert transformer.transform(True) is False
        assert transformer.transform(False) is True

    with subtests.test("not"):
        transformer = Transformer({
            '$': 'expr',
            'op': 'not',
        })

        assert transformer.transform(True) is False
        assert transformer.transform(False) is True
