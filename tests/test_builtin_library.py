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
    with pytest.raises(TransformationError, match='requires a string') as exc_info:
        _call('upper', 1)
    assert 'at template → call' in str(exc_info.value)


def test_split_rejects_no_content_sep():
    with pytest.raises(TransformationError, match='NO_CONTENT'):
        Transformer(
            {
                '$': 'split',
                'sep': {'$': 'get', 'name': 'missing'},
            },
        ).transform(['a', 'b'])


def test_regex_match_optional_groups_all_unmatched():
    assert _call('regex_match', values=['b', r'(a)?b']) == [None]


def test_b64encode_rejects_surrogate():
    with pytest.raises(TransformationError, match='UTF-8'):
        _call('b64encode', '\ud800')


def test_epoch_rejects_percent_space():
    with pytest.raises(TransformationError, match='directive'):
        _call('from_epoch', values=[0, '%Y% %m'])


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


def test_strip_variants_and_slice_edges():
    assert _call('strip', values=['xxhelloxx', 'x']) == 'hello'
    assert _call('lstrip', '  hi') == 'hi'
    assert _call('rstrip', 'hi  ') == 'hi'
    with pytest.raises(TransformationError, match='string or array'):
        _call('slice', values=[1, 0])
    with pytest.raises(TransformationError, match='stop must be an int'):
        _call('slice', values=['abc', 0, '1'])


def test_epoch_fmt_and_range_edges():
    with pytest.raises(TransformationError, match='must be a string'):
        _call('from_epoch', values=[0, 1])
    with pytest.raises(TransformationError, match='trailing'):
        _call('from_epoch', values=[0, '%Y-%'])
    with pytest.raises(TransformationError, match='out of range'):
        _call('from_epoch', 10 ** 20)
    # timezone-aware parse hits the astimezone branch
    assert isinstance(
        _call('to_epoch', values=['2024-01-01T00:00:00+0000', '%Y-%m-%dT%H:%M:%S%z']),
        int,
    )


def test_collection_type_guards():
    assert _call('length', {'a': 1}) == 1
    with pytest.raises(TransformationError, match='requires an array'):
        _call('flatten', 'nope')
    with pytest.raises(TransformationError, match='requires an array'):
        _call('sum', 'nope')
    with pytest.raises(TransformationError, match='requires an array'):
        _call('min', values=['nope'])
    with pytest.raises(TransformationError, match='1 or 2 arguments'):
        _call('min', values=[[1], 2, 3])
    with pytest.raises(TransformationError, match='1 or 2 arguments'):
        _call('max', values=[[1], 2, 3])
    assert _call('max', values=[[1, 5, 2]]) == 5
    assert _call('sorted', []) == []
    with pytest.raises(TransformationError, match='requires an array'):
        _call('sorted', 'abc')
    with pytest.raises(TransformationError, match='scalar elements'):
        _call('sorted', [[1], [2]])
    with pytest.raises(TransformationError, match='requires an array'):
        _call('unique', 'abc')
    with pytest.raises(TransformationError, match='requires a number'):
        _call('abs', 'x')
    with pytest.raises(TransformationError, match='ndigits must be an int'):
        _call('round', values=[1.5, '2'])
    assert _call('round', 1.5) == 2


def test_uuid5_and_regex_no_groups():
    ns = '6ba7b810-9dad-11d1-80b4-00c04fd430c8'  # NAMESPACE_DNS
    assert _call('uuid5', values=[ns, 'example.com']) == (
        'cfbff0d1-9375-5685-968c-48ce8b15ae17'
    )
    assert _call('regex_match', values=['abc', r'b']) == ['b']
    with pytest.raises(TransformationError, match='requires a string'):
        _call('regex_match', values=[1, 'a'])
    with pytest.raises(TransformationError, match='requires a string'):
        _call('regex_replace', values=['a', 1, 'x'])


def test_b64decode_non_utf8_payload():
    # encode raw bytes that are not valid UTF-8
    import base64
    payload = base64.b64encode(b'\xff\xfe').decode('ascii')
    with pytest.raises(TransformationError, match='not UTF-8'):
        _call('b64decode', payload)


def test_sorted_homogeneous_null_and_bool():
    # Python 3 refuses to order None against None.
    with pytest.raises(TransformationError, match='comparable'):
        _call('sorted', [None, None])
    assert _call('sorted', [True, False]) == [False, True]


def test_min_incomparable_elements():
    with pytest.raises(TransformationError, match='comparable'):
        _call('min', values=[[1, 'a']])
