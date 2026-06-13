from transon import Transformer


def test_zip_returns_lists_not_tuples():
    transformer = Transformer({
        '$': 'zip',
        'items': [[1, 2], [3, 4]],
    })
    result = transformer.transform(None)
    assert result == [[1, 3], [2, 4]]
    assert all(isinstance(row, list) for row in result)
