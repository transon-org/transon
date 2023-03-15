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
