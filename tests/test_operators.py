import pytest

from transon import Transformer


@pytest.mark.parametrize('op, left, right, expected', [
    ('and', 6, 3, 3),
    ('&&', 6, 3, 3),
    ('or', 0, 5, 5),
    ('||', 0, 5, 5),
    ('and', '', 'fallback', ''),
    ('or', '', 'fallback', 'fallback'),
])
def test_logical_and_or(op, left, right, expected):
    transformer = Transformer({
        '$': 'expr',
        'op': op,
        'value': right,
    })
    assert transformer.transform(left) == expected


def test_logical_and_values_reduce():
    transformer = Transformer({
        '$': 'expr',
        'op': 'and',
        'values': [6, 3],
    })
    assert transformer.transform(None) == 3
