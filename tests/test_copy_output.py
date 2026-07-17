import pytest

from transon import Transformer


def test_default_output_aliases_input():
    """By default a pass-through value is a reference into the input data."""
    data = {'a': {'nested': [1, 2, 3]}}
    transformer = Transformer({'$': 'attr', 'name': 'a'})
    result = transformer.transform(data)
    assert result is data['a']

    result['nested'].append(4)
    assert data['a']['nested'] == [1, 2, 3, 4]


def test_copy_output_breaks_aliasing():
    """`copy_output=True` returns a value that shares no structure with the input."""
    data = {'a': {'nested': [1, 2, 3]}}
    transformer = Transformer({'$': 'attr', 'name': 'a'})
    result = transformer.transform(data, copy_output=True)
    assert result == data['a']
    assert result is not data['a']
    assert result['nested'] is not data['a']['nested']

    result['nested'].append(4)
    assert data['a']['nested'] == [1, 2, 3]


def test_copy_output_with_this():
    data = [1, [2, 3]]
    transformer = Transformer({'$': 'this'})

    aliased = transformer.transform(data)
    assert aliased is data

    copied = transformer.transform(data, copy_output=True)
    assert copied == data
    assert copied is not data
    assert copied[1] is not data[1]


def test_copy_output_does_not_mutate_input():
    data = {'a': 1, 'b': [1, 2]}
    transformer = Transformer({'$': 'this'})
    before = {'a': 1, 'b': [1, 2]}
    transformer.transform(data, copy_output=True)
    assert data == before


@pytest.mark.parametrize('copy_output', [False, True])
def test_copy_output_preserves_value(copy_output):
    data = [{'x': 1}, {'x': 2}]
    transformer = Transformer({
        '$': 'map',
        'item': {'$': 'attr', 'name': 'x'},
    })
    result = transformer.transform(data, copy_output=copy_output)
    assert result == [1, 2]


def test_copy_output_keyword_only():
    """`copy_output` is keyword-only and must not collide with `no_content`."""
    data = {'$': 'attr', 'name': 'missing'}
    transformer = Transformer(data)
    assert transformer.transform({}, 'fallback', copy_output=True) == 'fallback'


def test_copy_output_preserves_no_content_identity():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    result = transformer.transform(
        {}, no_content=Transformer.NO_CONTENT, copy_output=True,
    )
    assert result is Transformer.NO_CONTENT


def test_copy_output_preserves_nested_no_content_identity():
    # A literal template list keeps NO_CONTENT elements (only container rules
    # skip them), so the sentinel can sit inside a deep-copied result.
    transformer = Transformer([{'$': 'attr', 'name': 'missing'}])
    result = transformer.transform({}, copy_output=True)
    assert result[0] is Transformer.NO_CONTENT


def test_copy_output_returns_substitute_unchanged():
    substitute = {'fallback': True}
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    result = transformer.transform({}, no_content=substitute, copy_output=True)
    assert result is substitute
