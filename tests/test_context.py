import pytest

from transon.transformers import Context, DefinitionError


def test_derive_does_not_eagerly_copy_parent_variables():
    parent = Context(this={'items': [1, 2]}, saved='root')
    child = parent.derive(this=1, index=0, item=1)

    assert 'saved' not in child._data
    assert 'saved' in child
    assert child['saved'] == 'root'


def test_first_set_materializes_inherited_variables():
    parent = Context(this=[1, 2], saved='root')
    child = parent.derive(this=1, index=0, item=1)

    child['local'] = 'child-only'

    assert child._materialized is True
    assert child._data['saved'] == 'root'
    assert child._data['local'] == 'child-only'
    assert 'local' not in parent._data


def test_child_set_does_not_mutate_parent_variable():
    parent = Context(this=[1, 2], saved='root')
    child = parent.derive(this=1, index=0, item=1)

    child['saved'] = 'overridden'

    assert parent['saved'] == 'root'
    assert child['saved'] == 'overridden'


def test_parent_chain_lookup_depth():
    root = Context(this={'n': 0})
    mid = root.derive(this={'n': 1})
    leaf = mid.derive(this={'n': 2})

    root['var'] = 'from-root'

    assert leaf['var'] == 'from-root'


def test_iteration_slots_visible_after_nested_derive():
    parent = Context(this=[{'id': 1}], item={'id': 1}, index=0)
    child = parent.derive(this={'id': 1})

    assert child.item == {'id': 1}
    assert child.index == 0
