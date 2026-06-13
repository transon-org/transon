import pytest

from transon import (
    Transformer,
    DefinitionError,
    TransformationError,
)


def test_attr_type_error_on_invalid_index():
    transformer = Transformer({'$': 'attr', 'name': 'x'})
    with pytest.raises(TransformationError, match='cannot access attribute'):
        transformer.transform('hello')


def test_attr_missing_key_returns_none_at_top_level():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    assert transformer.transform({'a': 1}) is None


def test_attr_missing_key_returns_raw_no_content_when_requested():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    assert transformer.transform(
        {'a': 1},
        no_content=transformer.NO_CONTENT,
    ) is transformer.NO_CONTENT


def test_zip_non_iterable_items():
    transformer = Transformer({'$': 'zip', 'items': 1})
    with pytest.raises(TransformationError, match='zip items must be iterable'):
        transformer.transform(None)


def test_expr_empty_values():
    transformer = Transformer({'$': 'expr', 'op': '+', 'values': []})
    with pytest.raises(DefinitionError, match='at least one element'):
        transformer.transform(0)


def test_expr_non_list_values():
    transformer = Transformer({'$': 'expr', 'op': '+', 'values': 'ab'})
    with pytest.raises(DefinitionError, match='must be a list'):
        transformer.transform(0)


def test_expr_incompatible_operands():
    transformer = Transformer({'$': 'expr', 'op': 'mod', 'value': 'x'})
    with pytest.raises(TransformationError, match='incompatible operands'):
        transformer.transform(1)


def test_call_non_list_values():
    transformer = Transformer({'$': 'call', 'name': 'int', 'values': 'FF'})
    with pytest.raises(DefinitionError, match='must be a list'):
        transformer.transform(None)


def test_call_incompatible_arguments():
    transformer = Transformer({'$': 'call', 'name': 'int', 'value': {}})
    with pytest.raises(TransformationError, match='incompatible arguments'):
        transformer.transform(None)


def test_format_missing_key():
    transformer = Transformer({'$': 'format', 'pattern': '{missing}'})
    with pytest.raises(TransformationError, match='missing key or index'):
        transformer.transform({'present': 1})


def test_item_outside_map():
    transformer = Transformer({'$': 'item'})
    with pytest.raises(DefinitionError, match='only valid inside'):
        transformer.transform([1, 2, 3])


def test_key_outside_map():
    transformer = Transformer({'$': 'key'})
    with pytest.raises(DefinitionError, match='only valid inside'):
        transformer.transform({'a': 1})


def test_parent_at_root():
    transformer = Transformer({'$': 'parent'})
    with pytest.raises(DefinitionError, match='root context'):
        transformer.transform(0)


def test_attr_no_content_name_on_list():
    transformer = Transformer({
        '$': 'attr',
        'name': {'$': 'get', 'name': 'missing'},
    })
    assert transformer.transform([1, 2, 3]) is None


def test_attr_no_content_path_segment():
    transformer = Transformer({
        '$': 'attr',
        'names': [{'$': 'get', 'name': 'missing'}, 'b'],
    })
    assert transformer.transform({'a': {'b': 1}}) is None


def test_set_no_content_name():
    transformer = Transformer({'$': 'set', 'name': {'$': 'get', 'name': 'missing'}})
    with pytest.raises(TransformationError, match='variable name cannot be no value'):
        transformer.transform(1)


def test_get_no_content_name():
    transformer = Transformer({'$': 'get', 'name': {'$': 'get', 'name': 'missing'}})
    with pytest.raises(TransformationError, match='variable name cannot be no value'):
        transformer.transform(1)


def test_object_fields_not_a_mapping():
    transformer = Transformer({'$': 'object', 'fields': 5})
    with pytest.raises(DefinitionError, match='`fields` must be a mapping'):
        transformer.transform(None)


def test_object_without_any_mode():
    transformer = Transformer({'$': 'object'})
    with pytest.raises(DefinitionError, match='`key` property is required'):
        transformer.transform(None)


def test_join_dynamic_sep_non_string():
    transformer = Transformer({
        '$': 'join',
        'items': ['a', 'b'],
        'sep': {'$': 'attr', 'name': 'sep'},
    })
    with pytest.raises(TransformationError, match='must evaluate to a string'):
        transformer.transform({'sep': 42})


def test_format_dynamic_pattern_non_string():
    transformer = Transformer({
        '$': 'format',
        'pattern': {'$': 'attr', 'name': 'pattern'},
    })
    with pytest.raises(TransformationError, match='must evaluate to a string'):
        transformer.transform({'pattern': 123})
