import pytest

from transon import Transformer


@pytest.mark.parametrize(['data_type', 'data'], [
    (dict, {'a': 1}),
    (list, [1, 2, 3]),
    (str, 'test'),
    (int, 123),
])
def test_this_simple(data_type, data):
    transformer = Transformer({
        '$': 'this'
    })
    result = transformer.transform(data)
    assert isinstance(result, data_type)
    assert result is data
