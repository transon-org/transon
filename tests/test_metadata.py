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
    assert set(metadata['docs']) == {
        'rules', 'operators', 'functions', 'worked_examples', 'recipes',
    }


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
    assert name_param['options'] == ['str', 'int', 'float', 'type']


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


def _catalog_param(metadata, rule_name, param_name):
    rule = next(
        rule for rule in metadata['catalog']['rules']
        if rule['name'] == rule_name
    )
    return next(p for p in rule['params'] if p['name'] == param_name)


# Roadmap R-28: structural param facts (`container` + `arm`) in the export.

def test_metadata_version_is_current():
    assert METADATA_VERSION == '2.2'
    assert get_editor_metadata()['metadata_version'] == '2.2'


def test_list_container_exported():
    metadata = get_editor_metadata()
    funcs = _catalog_param(metadata, 'chain', 'funcs')
    assert funcs['container'] == 'list'
    assert 'arm' not in funcs


def test_mapping_container_exported():
    metadata = get_editor_metadata()
    for rule_name, param_name in (('object', 'fields'), ('switch', 'cases')):
        param = _catalog_param(metadata, rule_name, param_name)
        assert param['container'] == 'mapping'
        assert 'arm' not in param


def test_arms_container_exports_arm_schema():
    metadata = get_editor_metadata()
    cases = _catalog_param(metadata, 'cond', 'cases')
    assert cases['container'] == 'arms'
    assert cases['arm']['required'] == ['when', 'then']
    slots = cases['arm']['params']
    assert [slot['name'] for slot in slots] == ['when', 'then']
    for slot in slots:
        assert slot['kind'] == 'dynamic'
        assert 'container' not in slot
        assert 'options' not in slot
        assert 'arm' not in slot


def test_template_params_have_no_container_or_arm():
    annotated = {
        ('chain', 'funcs'),
        ('object', 'fields'),
        ('switch', 'cases'),
        ('cond', 'cases'),
    }
    metadata = get_editor_metadata()
    for rule in metadata['catalog']['rules']:
        for param in rule['params']:
            if (rule['name'], param['name']) in annotated:
                continue
            assert 'container' not in param, (rule['name'], param['name'])
            assert 'arm' not in param, (rule['name'], param['name'])


def test_docs_payload_carries_arm_slot_descriptions():
    metadata = get_editor_metadata()
    docs_cond = next(
        rule for rule in metadata['docs']['rules']
        if rule['name'] == 'cond'
    )
    cases = next(p for p in docs_cond['params'] if p['name'] == 'cases')
    assert [slot['name'] for slot in cases['arms']] == ['when', 'then']
    for slot in cases['arms']:
        assert slot['description']


def test_docs_params_without_arms_have_no_arms_key():
    metadata = get_editor_metadata()
    for rule in metadata['docs']['rules']:
        for param in rule['params']:
            if (rule['name'], param['name']) == ('cond', 'cases'):
                continue
            assert 'arms' not in param, (rule['name'], param['name'])


# Roadmap R-29: example tags + curated example tiers in the export.

TIER_TAGS = {'worked-example', 'recipe'}


def _assert_examples_tagged(examples, owner):
    for example in examples:
        assert isinstance(example.get('tags'), list), (owner, example['name'])
        assert example['tags'], (owner, example['name'])


def test_rule_and_param_examples_carry_tags():
    metadata = get_editor_metadata()
    for rule in metadata['docs']['rules']:
        _assert_examples_tagged(rule['examples'], rule['name'])
        for param in rule['params']:
            _assert_examples_tagged(
                param['examples'], (rule['name'], param['name']),
            )


def test_operator_and_function_examples_carry_tags():
    metadata = get_editor_metadata()
    for entry in metadata['docs']['operators']:
        _assert_examples_tagged(entry['examples'], entry['name'])
    for entry in metadata['docs']['functions']:
        _assert_examples_tagged(entry['examples'], entry['name'])


def test_curated_tier_blocks_exported():
    metadata = get_editor_metadata()
    for block in ('worked_examples', 'recipes'):
        examples = metadata['docs'][block]
        assert examples, f'docs.{block} must not be empty'
        for example in examples:
            assert set(example) == {
                'name', 'doc', 'template', 'data', 'result', 'tags',
            }


def test_curated_cases_carry_only_their_tier_tag():
    metadata = get_editor_metadata()
    for block, tier_tag in (
        ('worked_examples', 'worked-example'),
        ('recipes', 'recipe'),
    ):
        for example in metadata['docs'][block]:
            assert example['tags'] == [tier_tag], example['name']


def test_reference_examples_never_carry_a_tier_tag():
    metadata = get_editor_metadata()
    for rule in metadata['docs']['rules']:
        for example in rule['examples']:
            assert not TIER_TAGS & set(example['tags']), (
                rule['name'], example['name'],
            )
        for param in rule['params']:
            for example in param['examples']:
                assert not TIER_TAGS & set(example['tags']), (
                    rule['name'], param['name'], example['name'],
                )
    for block in ('operators', 'functions'):
        for entry in metadata['docs'][block]:
            for example in entry['examples']:
                assert not TIER_TAGS & set(example['tags']), (
                    block, entry['name'], example['name'],
                )
