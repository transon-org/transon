import pytest

from transon import Transformer, TransformationError
from transon.docs import get_functions_docs, get_operators_docs


NEW_FUNCTIONS = {
    'upper', 'lower', 'capitalize', 'replace', 'removeprefix', 'removesuffix',
    'strip', 'lstrip', 'rstrip', 'slice', 'from_epoch', 'to_epoch', 'length',
    'flatten', 'sum', 'min', 'max', 'sorted', 'reversed', 'unique', 'abs',
    'floor', 'ceil', 'round', 'bool', 'b64encode', 'b64decode', 'uuid5',
    'regex_match', 'regex_replace',
}


def test_new_functions_present_in_docs():
    documented = {entry['name'] for entry in get_functions_docs()}
    assert NEW_FUNCTIONS <= documented
    for entry in get_functions_docs():
        if entry['name'] in NEW_FUNCTIONS:
            assert entry['doc'] and 'TBD' not in entry['doc']


def test_in_operator_present_in_docs():
    names = {entry['name'] for entry in get_operators_docs()}
    assert 'in' in names


def _call(name, data=None, *, value=None, values=None):
    template = {'$': 'call', 'name': name}
    if value is not None:
        template['value'] = value
    if values is not None:
        template['values'] = values
    return Transformer(template).transform(data)


def test_upper_rejects_non_string():
    with pytest.raises(TransformationError, match='requires a string'):
        _call('upper', 1)


def test_split_empty_sep_raises_transformation_error():
    with pytest.raises(TransformationError, match='non-empty string'):
        Transformer({'$': 'split', 'sep': ''}).transform('a/b')


def test_split_no_content_passthrough():
    result = Transformer(
        {
            '$': 'chain',
            'funcs': [
                {'$': 'attr', 'name': 'missing'},
                {'$': 'split', 'sep': '/'},
            ],
        },
    ).transform({}, no_content=Transformer.NO_CONTENT)
    assert result is Transformer.NO_CONTENT


def test_split_rejects_non_string_non_array():
    with pytest.raises(TransformationError, match='string or array'):
        Transformer({'$': 'split', 'sep': '/'}).transform(1)


def test_split_empty_array_sep_raises():
    with pytest.raises(TransformationError, match='non-empty array'):
        Transformer({'$': 'split', 'sep': []}).transform([1, 2])


def test_min_empty_without_default_raises():
    with pytest.raises(TransformationError, match='empty array'):
        _call('min', values=[[]])


def test_min_empty_with_default():
    assert _call('min', values=[[], 42]) == 42


def test_sorted_mixed_types_raises():
    with pytest.raises(TransformationError, match='homogeneous'):
        _call('sorted', [1, 'a'])


def test_flatten_rejects_non_array_element():
    with pytest.raises(TransformationError, match='every element'):
        _call('flatten', [[1], 2])


def test_sum_rejects_bool():
    with pytest.raises(TransformationError, match='numeric'):
        _call('sum', [True])


def test_from_epoch_rejects_nan():
    with pytest.raises(TransformationError, match='non-finite'):
        _call('from_epoch', float('nan'))


def test_from_epoch_rejects_locale_directive():
    with pytest.raises(TransformationError, match='directive'):
        _call('from_epoch', values=[0, '%Y-%b'])


def test_to_epoch_rejects_bad_parse():
    with pytest.raises(TransformationError, match='failed to parse'):
        _call('to_epoch', values=['not-a-date'])


def test_slice_rejects_non_int_index():
    with pytest.raises(TransformationError, match='start must be an int'):
        _call('slice', values=['abc', '1'])


def test_unique_rejects_object_element():
    with pytest.raises(TransformationError, match='rejects object'):
        _call('unique', [{'a': 1}])


def test_b64decode_invalid_raises():
    with pytest.raises(TransformationError, match='invalid base64'):
        _call('b64decode', '!!!')


def test_uuid5_bad_namespace_raises():
    with pytest.raises(TransformationError, match='namespace'):
        _call('uuid5', values=['nope', 'x'])


def test_regex_match_invalid_pattern_raises():
    with pytest.raises(TransformationError, match='invalid pattern'):
        _call('regex_match', values=['abc', '('])


def test_regex_replace_invalid_pattern_raises():
    with pytest.raises(TransformationError, match='invalid pattern'):
        _call('regex_replace', values=['abc', '(', 'x'])


def test_in_operator_is_total():
    assert Transformer({'$': 'expr', 'op': 'in', 'value': [1, 2]}).transform(3) is False
    assert Transformer({'$': 'expr', 'op': 'in', 'value': 'abc'}).transform(1) is False
    assert Transformer({'$': 'expr', 'op': 'in', 'value': {'a': 1}}).transform(1) is False
    assert Transformer({'$': 'expr', 'op': 'in', 'value': 5}).transform(1) is False


def test_length_rejects_number():
    with pytest.raises(TransformationError, match='string, array, or object'):
        _call('length', 5)


def test_reversed_rejects_object():
    with pytest.raises(TransformationError, match='string or array'):
        _call('reversed', {'a': 1})


def test_from_epoch_truncates_fractional_seconds():
    assert _call('from_epoch', 1.9) == '1970-01-01T00:00:01Z'


def test_no_bare_value_error_from_min():
    with pytest.raises(TransformationError):
        _call('min', values=[[]])
    # Ensure it is not a raw ValueError escaping the call wrapper.
    try:
        _call('min', values=[[]])
    except TransformationError:
        pass
    except ValueError:  # pragma: no cover
        pytest.fail('bare ValueError escaped rule_call')
