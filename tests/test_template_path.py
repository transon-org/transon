import pytest

from transon import Transformer, DefinitionError, TransformationError


def test_transformation_error_includes_nested_template_path():
    template = {
        'pipeline': {
            '$': 'chain',
            'funcs': [
                {
                    '$': 'map',
                    'item': {'$': 'attr', 'name': 'missing'},
                },
            ],
        },
    }
    transformer = Transformer(template)
    with pytest.raises(TransformationError) as exc_info:
        transformer.transform('not-a-list')

    message = str(exc_info.value)
    assert 'value is not iterable' in message
    assert 'at template → pipeline → chain → funcs[0] → map' in message


def test_definition_error_includes_rule_location():
    template = {'$': 'item'}
    transformer = Transformer(template)
    with pytest.raises(DefinitionError) as exc_info:
        transformer.transform([1, 2, 3])

    message = str(exc_info.value)
    assert 'only valid inside' in message
    assert 'at template → item' in message


def test_validate_error_includes_nested_path():
    template = {
        'used': {'$': 'attr', 'name': 'x'},
        'dead': {'$': 'attr', 'nmae': 'y'},
    }
    transformer = Transformer(template)
    with pytest.raises(DefinitionError) as exc_info:
        transformer.validate()

    message = str(exc_info.value)
    assert 'unknown `nmae`' in message
    assert 'at template → dead → attr' in message


def test_chain_nested_attr_error_path():
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'attr', 'name': {'$': 'expr', 'op': 'mod', 'value': 'x'}},
        ],
    }
    transformer = Transformer(template)
    with pytest.raises(TransformationError) as exc_info:
        transformer.transform(7)

    message = str(exc_info.value)
    assert 'incompatible operands' in message
    assert 'at template → chain → funcs[0] → attr → name → expr' in message
