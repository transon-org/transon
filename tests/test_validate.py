import pytest

from transon import Transformer, DefinitionError


def test_validate_accepts_valid_template():
    Transformer({'$': 'attr', 'name': 'x'}).validate()


def test_validate_unknown_parameter():
    transformer = Transformer({'$': 'attr', 'nmae': 'x'})

    with pytest.raises(DefinitionError, match='unknown `nmae`'):
        transformer.validate()


def test_validate_missing_required_parameter():
    transformer = Transformer({'$': 'attr'})

    with pytest.raises(DefinitionError, match='no valid parameter combination'):
        transformer.validate()


def test_validate_ambiguous_attr_parameters():
    transformer = Transformer({'$': 'attr', 'name': 'x', 'names': ['x']})

    with pytest.raises(DefinitionError, match='ambiguous mutually exclusive'):
        transformer.validate()


def test_validate_ambiguous_map_parameters():
    transformer = Transformer({'$': 'map', 'item': 1, 'key': 2, 'value': 3})

    with pytest.raises(DefinitionError, match='ambiguous mutually exclusive'):
        transformer.validate()


def test_validate_incomplete_map_key_value():
    transformer = Transformer({'$': 'map', 'key': {'$': 'key'}})

    with pytest.raises(DefinitionError, match='incomplete parameter set'):
        transformer.validate()


def test_validate_ambiguous_expr_parameters():
    transformer = Transformer(
        {'$': 'expr', 'op': 'add', 'value': 1, 'values': [1, 2]}
    )

    with pytest.raises(DefinitionError, match='ambiguous mutually exclusive'):
        transformer.validate()


def test_validate_unknown_rule():
    transformer = Transformer({'$': 'missing_rule'})

    with pytest.raises(DefinitionError, match='Invalid rule'):
        transformer.validate()


def test_validate_invalid_operator_literal():
    transformer = Transformer({'$': 'expr', 'op': 'missing_op'})

    with pytest.raises(DefinitionError, match='Invalid operator'):
        transformer.validate()


def test_validate_invalid_function_literal():
    transformer = Transformer({'$': 'call', 'name': 'missing_fn'})

    with pytest.raises(DefinitionError, match='Invalid function'):
        transformer.validate()


def test_validate_object_fields_literal_marker_key_ok():
    Transformer(
        {'$': 'object', 'fields': {'$': {'$': 'attr', 'name': 'x'}}}
    ).validate()


def test_validate_object_fields_recurses_into_values():
    transformer = Transformer(
        {'$': 'object', 'fields': {'$': {'$': 'attr', 'nmae': 'x'}}}
    )

    with pytest.raises(DefinitionError, match='unknown `nmae`'):
        transformer.validate()


def test_validate_object_ambiguous_modes():
    transformer = Transformer(
        {'$': 'object', 'key': 'a', 'value': 'b', 'fields': {}}
    )

    with pytest.raises(DefinitionError, match='ambiguous mutually exclusive'):
        transformer.validate()


def test_validate_chain_funcs_must_be_list():
    transformer = Transformer({'$': 'chain', 'funcs': {'$': 'this'}})

    with pytest.raises(DefinitionError, match='`funcs` must be a list'):
        transformer.validate()


def test_validate_accepts_valid_constant_and_containers():
    # Exercises: valid operator-domain constant, a list-valued dynamic param,
    # the `chain` list container, and the `cond` arms container.
    Transformer({'$': 'expr', 'op': '+', 'value': 1}).validate()
    Transformer({'$': 'expr', 'op': '+', 'values': [{'$': 'this'}, 1]}).validate()
    Transformer({'$': 'chain', 'funcs': [{'$': 'this'}]}).validate()
    Transformer(
        {'$': 'cond', 'cases': [{'when': True, 'then': 1}], 'default': 0}
    ).validate()


def test_validate_non_string_constant_is_skipped():
    Transformer({'$': 'expr', 'op': {'$': 'this'}, 'value': 1}).validate()


def test_validate_cond_cases_must_be_list():
    transformer = Transformer({'$': 'cond', 'cases': 5})

    with pytest.raises(DefinitionError, match='`cases` must be a list'):
        transformer.validate()


def test_validate_cond_recurses_into_arm_templates():
    transformer = Transformer({
        '$': 'cond',
        'cases': [{'when': {'$': 'attr', 'nmae': 'x'}, 'then': 1}],
    })

    with pytest.raises(DefinitionError, match='unknown `nmae`'):
        transformer.validate()


def test_validate_nested_dead_branch_typo():
    transformer = Transformer({
        'used': {'$': 'attr', 'name': 'x'},
        'dead': {'$': 'attr', 'nmae': 'y'},
    })

    with pytest.raises(DefinitionError, match='unknown `nmae`'):
        transformer.validate()


def test_validate_init_flag():
    with pytest.raises(DefinitionError, match='unknown `nmae`'):
        Transformer({'$': 'attr', 'nmae': 'x'}, validate=True)


def test_validate_custom_rule_schema():
    class ExtendedTransformer(Transformer):
        pass

    @ExtendedTransformer.register_rule(
        'typed',
        _variants=[{'field'}],
        field='Required field.',
    )
    def rule_typed(_t, _template, _context):
        return None

    ExtendedTransformer({'$': 'typed', 'field': 'x'}, validate=True)

    with pytest.raises(DefinitionError, match='`field` property is required'):
        ExtendedTransformer({'$': 'typed'}, validate=True)
