"""Roadmap R-27 — `include` propagates the loader/context through construction.

`include` always calls the `template_loader` as `loader(name, context=IncludeContext)`.
The loader constructs the sub-`Transformer` from the context, so the parent's
loader/marker/depth/stack are applied at construction time instead of by mutating the
loaded instance.
"""
import dataclasses

import pytest

from transon import (
    Transformer,
    IncludeContext,
    TransformationError,
)


def test_context_loader_propagates_parent_loader_for_recursion():
    """A self-`include`ing codec recurses without the loader re-passing itself."""
    templates = {
        'walk': {
            '$': 'switch',
            'key': {'$': 'call', 'name': 'type', 'value': {'$': 'this'}},
            'cases': {
                'array': {'$': 'map', 'item': {'$': 'include', 'name': 'walk'}},
            },
            'default': {'$': 'this'},
        },
    }

    def loader(name, context=None):
        return context.transformer(templates[name])

    parent = Transformer({'$': 'include', 'name': 'walk'}, template_loader=loader)
    assert parent.transform([1, [2, 3], 4]) == [1, [2, 3], 4]


def test_context_loader_propagates_depth_and_stack():
    """`max_include_depth` and the include-stack cross the boundary via construction."""
    templates = {'loop': {'$': 'include', 'name': 'loop'}}

    def loader(name, context=None):
        return context.transformer(templates[name])

    parent = Transformer(
        {'$': 'include', 'name': 'loop'},
        template_loader=loader,
        max_include_depth=3,
    )
    with pytest.raises(
        TransformationError,
        match=r'include depth limit \(3\) exceeded: loop → loop → loop → loop',
    ):
        parent.transform(None)


def test_context_loader_inherits_parent_marker_by_default():
    """`context.transformer` defaults the sub-template marker to the parent's."""
    def loader(_name, context=None):
        return context.transformer({'@': 'this'})

    parent = Transformer(
        {'@': 'include', 'name': 'sub'},
        marker='@',
        template_loader=loader,
    )
    assert parent.transform('hello') == 'hello'


def test_context_loader_can_pin_a_different_marker():
    """A loader may pin a non-default marker for the sub-template explicitly."""
    def loader(_name, context=None):
        return context.transformer({'#': 'this'}, marker='#')

    parent = Transformer(
        {'@': 'include', 'name': 'sub'},
        marker='@',
        template_loader=loader,
    )
    assert parent.transform('hi') == 'hi'


def test_context_loader_instance_is_not_mutated_by_engine():
    """The engine never reassigns attributes on the loaded instance (no mutation)."""
    captured = {}

    def loader(_name, context=None):
        sub = context.transformer('leaf-value')
        captured['instance'] = sub
        captured['stack'] = list(sub._include_stack)
        captured['marker'] = sub.marker
        captured['depth'] = sub.max_include_depth
        captured['loader'] = sub.template_loader
        return sub

    parent = Transformer(
        {'$': 'include', 'name': 'leaf'},
        template_loader=loader,
        max_include_depth=11,
    )
    assert parent.transform('x') == 'leaf-value'

    sub = captured['instance']
    assert sub._include_stack == captured['stack']
    assert sub.marker == captured['marker']
    assert sub.max_include_depth == captured['depth']
    assert sub.template_loader is captured['loader']
    assert sub.max_include_depth == 11


def test_include_context_is_frozen():
    context = IncludeContext(
        template_loader=lambda name, context=None: None,
        marker='$',
        max_include_depth=50,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.marker = '@'
