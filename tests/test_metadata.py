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
        'examples', 'rules', 'operators', 'functions',
        'worked_examples', 'recipes',
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
    assert METADATA_VERSION == '3.0'
    assert get_editor_metadata()['metadata_version'] == '3.0'


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


# Roadmap R-29 (tags + curated tiers) reshaped by R-31 (flat corpus + name
# references): docs.examples carries every case exactly once; every other
# examples field is an ordered list of name references into it.

TIER_TAGS = {'worked-example', 'recipe'}


def _corpus_by_name(metadata):
    corpus = metadata['docs']['examples']
    return {example['name']: example for example in corpus}


def _iter_reference_lists(metadata):
    """Yield ``(owner, name_list)`` for every reference-example field."""
    docs_payload = metadata['docs']
    for rule in docs_payload['rules']:
        yield rule['name'], rule['examples']
        for param in rule['params']:
            yield (rule['name'], param['name']), param['examples']
    for block in ('operators', 'functions'):
        for entry in docs_payload[block]:
            yield (block, entry['name']), entry['examples']


def test_corpus_entries_carry_full_shape_and_tags():
    metadata = get_editor_metadata()
    corpus = metadata['docs']['examples']
    assert corpus, 'docs.examples must not be empty'
    for example in corpus:
        assert set(example) == {
            'name', 'doc', 'template', 'data', 'result', 'tags',
        }
        assert isinstance(example['tags'], list), example['name']
        assert example['tags'], example['name']


def test_corpus_names_are_unique():
    metadata = get_editor_metadata()
    names = [example['name'] for example in metadata['docs']['examples']]
    assert len(names) == len(set(names))


def test_every_reference_resolves_into_the_corpus():
    metadata = get_editor_metadata()
    by_name = _corpus_by_name(metadata)
    for owner, name_list in _iter_reference_lists(metadata):
        assert isinstance(name_list, list), owner
        for name in name_list:
            assert isinstance(name, str), (owner, name)
            assert name in by_name, (owner, name)
    for block in ('worked_examples', 'recipes'):
        for name in metadata['docs'][block]:
            assert name in by_name, (block, name)


def test_every_corpus_case_is_reachable():
    metadata = get_editor_metadata()
    referenced = set()
    for _, name_list in _iter_reference_lists(metadata):
        referenced.update(name_list)
    referenced.update(metadata['docs']['worked_examples'])
    referenced.update(metadata['docs']['recipes'])
    corpus_names = {ex['name'] for ex in metadata['docs']['examples']}
    orphans = corpus_names - referenced
    assert not orphans, f'corpus cases referenced nowhere: {sorted(orphans)}'


def test_curated_tier_blocks_exported():
    metadata = get_editor_metadata()
    by_name = _corpus_by_name(metadata)
    for block, tier_tag in (
        ('worked_examples', 'worked-example'),
        ('recipes', 'recipe'),
    ):
        names = metadata['docs'][block]
        assert names, f'docs.{block} must not be empty'
        for name in names:
            assert by_name[name]['tags'] == [tier_tag], name


def test_reference_examples_never_carry_a_tier_tag():
    metadata = get_editor_metadata()
    by_name = _corpus_by_name(metadata)
    for owner, name_list in _iter_reference_lists(metadata):
        for name in name_list:
            assert not TIER_TAGS & set(by_name[name]['tags']), (owner, name)
