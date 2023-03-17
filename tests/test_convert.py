from transon import Transformer


def test_convert_with_values():
    transformer = Transformer({
        '$': 'convert',
        'name': 'int',
        'values': [
            {'$': 'this'},
            16
        ]
    })

    assert transformer.transform("FF") == 255
