import pytest

from transon import Transformer, DefinitionError
from transon.metadata import (
    METADATA_VERSION,
    derive_variants,
    get_editor_metadata,
)


def test_get_editor_metadata_shape():
    metadata = get_editor_metadata()
    assert metadata['metadata_version'] == METADATA_VERSION
    assert 'engine_version' in metadata
    assert set(metadata) == {
        'metadata_version', 'engine_version', 'catalog', 'docs',
    }
    assert set(metadata['catalog']) == {'rules', 'operators', 'functions'}
    assert set(metadata['docs']) == {'rules', 'operators', 'functions'}


def test_attr_variants_pre_derived():
    rule = Transformer.get_rule('attr')
    variants = derive_variants(rule)
    assert variants == [
        {
            'id': 'name',
            'params': [
                {'name': 'name', 'required': True},
                {'name': 'default', 'required': False},
            ],
        },
        {
            'id': 'names',
            'params': [
                {'name': 'names', 'required': True},
                {'name': 'default', 'required': False},
            ],
        },
    ]


def test_expr_op_options_resolved():
    metadata = get_editor_metadata()
    expr = next(
        rule for rule in metadata['catalog']['rules']
        if rule['name'] == 'expr'
    )
    op_param = next(param for param in expr['params'] if param['name'] == 'op')
    assert op_param['kind'] == 'constant'
    assert 'lt' in op_param['options']
    assert '<' in op_param['options']


def test_call_name_options_resolved():
    metadata = get_editor_metadata()
    call = next(
        rule for rule in metadata['catalog']['rules']
        if rule['name'] == 'call'
    )
    name_param = next(
        param for param in call['params'] if param['name'] == 'name'
    )
    assert name_param['kind'] == 'constant'
    assert name_param['options'] == ['str', 'int', 'float']


def test_docs_payload_joins_by_name():
    metadata = get_editor_metadata()
    catalog_attr = next(
        rule for rule in metadata['catalog']['rules']
        if rule['name'] == 'attr'
    )
    docs_attr = next(
        rule for rule in metadata['docs']['rules']
        if rule['name'] == 'attr'
    )
    assert catalog_attr['name'] == docs_attr['name']
    assert docs_attr['description']
    assert isinstance(docs_attr['examples'], list)


def test_switch_and_cond_in_catalog():
    metadata = get_editor_metadata()
    rule_names = {rule['name'] for rule in metadata['catalog']['rules']}
    assert {'switch', 'cond'}.issubset(rule_names)


def test_validate_switch_malformed_arm():
    transformer = Transformer({
        '$': 'cond',
        'cases': [
            {'when': True},
        ],
    })
    with pytest.raises(DefinitionError, match='must include `when` and `then`'):
        transformer.validate()


def test_validate_switch_cases_must_be_mapping():
    transformer = Transformer({
        '$': 'switch',
        'key': 'a',
        'cases': [],
    })
    with pytest.raises(DefinitionError, match='must be a mapping'):
        transformer.validate()


def test_dynamic_param_has_kind_and_no_options():
    metadata = get_editor_metadata()
    attr = next(
        rule for rule in metadata['catalog']['rules']
        if rule['name'] == 'attr'
    )
    name_param = next(p for p in attr['params'] if p['name'] == 'name')
    assert name_param['kind'] == 'dynamic'
    assert 'options' not in name_param
