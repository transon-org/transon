import pytest

from transon import Transformer, DefinitionError


def _t(template, data, **kwargs):
    return Transformer(template, **kwargs).transform(data)


def test_switch_matches_case():
    result = _t(
        {'$': 'switch', 'key': {'$': 'this'}, 'cases': {'a': 'A', 'b': 'B'}},
        'b',
    )
    assert result == 'B'


def test_switch_default_when_no_match():
    result = _t(
        {'$': 'switch', 'key': {'$': 'this'}, 'cases': {'a': 'A'}, 'default': 'D'},
        'z',
    )
    assert result == 'D'


def test_switch_no_match_no_default_is_none():
    result = _t(
        {'$': 'switch', 'key': {'$': 'this'}, 'cases': {'a': 'A'}},
        'z',
    )
    assert result is None


def test_switch_unhashable_key_falls_through():
    result = _t(
        {'$': 'switch', 'key': {'$': 'this'}, 'cases': {}, 'default': 'D'},
        [1, 2, 3],
    )
    assert result == 'D'


def test_switch_only_selected_branch_is_walked():
    # The non-selected case contains a `parent` at root, which would raise if walked.
    result = _t(
        {
            '$': 'switch',
            'key': {'$': 'this'},
            'cases': {'a': 'A', 'b': {'$': 'parent'}},
        },
        'a',
    )
    assert result == 'A'


def test_switch_cases_must_be_mapping_at_transform():
    with pytest.raises(DefinitionError, match='`cases` must be a mapping'):
        _t({'$': 'switch', 'key': 'a', 'cases': 5}, None)


def test_cond_first_truthy_arm():
    result = _t(
        {
            '$': 'cond',
            'cases': [
                {'when': {'$': 'expr', 'op': '<', 'value': 0}, 'then': 'neg'},
                {'when': {'$': 'expr', 'op': '==', 'value': 0}, 'then': 'zero'},
            ],
            'default': 'pos',
        },
        0,
    )
    assert result == 'zero'


def test_cond_default_when_no_arm_matches():
    result = _t(
        {'$': 'cond', 'cases': [{'when': False, 'then': 'x'}], 'default': 'D'},
        None,
    )
    assert result == 'D'


def test_cond_no_match_no_default_is_none():
    result = _t(
        {'$': 'cond', 'cases': [{'when': False, 'then': 'x'}]},
        None,
    )
    assert result is None


def test_cond_no_content_when_is_falsy():
    result = _t(
        {
            '$': 'cond',
            'cases': [
                {'when': {'$': 'get', 'name': 'missing'}, 'then': 'first'},
                {'when': True, 'then': 'second'},
            ],
        },
        None,
    )
    assert result == 'second'


def test_cond_only_selected_then_is_walked():
    result = _t(
        {
            '$': 'cond',
            'cases': [
                {'when': True, 'then': 'ok'},
                {'when': True, 'then': {'$': 'parent'}},
            ],
        },
        None,
    )
    assert result == 'ok'


def test_cond_cases_must_be_list_at_transform():
    with pytest.raises(DefinitionError, match='`cases` must be a list'):
        _t({'$': 'cond', 'cases': 5}, None)


def test_cond_malformed_arm_at_transform():
    with pytest.raises(DefinitionError, match='must include `when` and `then`'):
        _t({'$': 'cond', 'cases': [{'when': True}]}, None)
