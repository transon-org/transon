import pytest

from transon import (
    Transformer,
    DefinitionError,
    TransformationError,
)


def test_include_without_loader_raises_definition_error():
    transformer = Transformer({'$': 'include', 'name': 'MissingTemplate'})

    with pytest.raises(DefinitionError, match='was not found'):
        transformer.transform(0)


def _cycle_loader(name):
    templates = {
        'A': {'$': 'include', 'name': 'B'},
        'B': {'$': 'include', 'name': 'A'},
    }
    return Transformer(templates[name], template_loader=_cycle_loader)


def test_include_cycle_raises_transformation_error_with_chain():
    transformer = Transformer(
        {'$': 'include', 'name': 'A'},
        template_loader=_cycle_loader,
        max_include_depth=10,
    )

    with pytest.raises(
        TransformationError,
        match=r'include depth limit \(10\) exceeded: A → B → A',
    ):
        transformer.transform(0)


def _linear_loader(name):
    templates = {
        '1': {'$': 'include', 'name': '2'},
        '2': {'$': 'include', 'name': '3'},
        '3': 'leaf',
    }
    return Transformer(templates[name], template_loader=_linear_loader)


def test_include_depth_limit_raises_transformation_error_with_chain():
    transformer = Transformer(
        {'$': 'include', 'name': '1'},
        template_loader=_linear_loader,
        max_include_depth=2,
    )

    with pytest.raises(
        TransformationError,
        match=r'include depth limit \(2\) exceeded: 1 → 2 → 3',
    ):
        transformer.transform(None)


def test_include_respects_custom_depth_limit():
    transformer = Transformer(
        {'$': 'include', 'name': '1'},
        template_loader=_linear_loader,
        max_include_depth=3,
    )

    assert transformer.transform(None) == 'leaf'
