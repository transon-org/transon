import pytest

from transon import Transformer


def test_transform_maps_no_content_to_none_by_default():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    assert transformer.transform({'a': 1}) is None


def test_transform_no_content_substitute():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    assert transformer.transform({'a': 1}, no_content='__missing__') == '__missing__'


def test_transform_no_content_raw_sentinel():
    transformer = Transformer({'$': 'attr', 'name': 'missing'})
    assert transformer.transform(
        {'a': 1},
        no_content=transformer.NO_CONTENT,
    ) is transformer.NO_CONTENT


def test_join_skips_no_content_items():
    transformer = Transformer({
        '$': 'join',
        'items': [
            {'$': 'attr', 'name': 'first'},
            {'$': 'attr', 'name': 'missing'},
            {'$': 'attr', 'name': 'second'},
        ],
        'sep': ', ',
    })
    assert transformer.transform({
        'first': 'hello',
        'second': 'world',
    }) == 'hello, world'


def test_join_all_no_content_items_yields_no_content():
    transformer = Transformer({
        '$': 'join',
        'items': [
            {'$': 'attr', 'name': 'missing_a'},
            {'$': 'attr', 'name': 'missing_b'},
        ],
    })
    assert transformer.transform({}) is None


def test_join_empty_items_yields_no_content():
    transformer = Transformer({
        '$': 'join',
        'items': [],
    })
    assert transformer.transform({}) is None


def test_join_empty_items_with_default():
    transformer = Transformer({
        '$': 'join',
        'items': [],
        'default': {},
    })
    assert transformer.transform({}) == {}


def test_no_content_is_falsy():
    assert not Transformer.NO_CONTENT


def test_expr_or_falls_back_from_no_content():
    transformer = Transformer({
        '$': 'expr',
        'op': 'or',
        'values': [
            {'$': 'attr', 'name': 'missing'},
            {'fallback': True},
        ],
    })
    assert transformer.transform({}) == {'fallback': True}


def test_join_empty_or_fallback_via_chain():
    transformer = Transformer({
        '$': 'chain',
        'funcs': [
            {'$': 'join', 'items': []},
            {'$': 'expr', 'op': 'or', 'value': {'empty': True}},
        ],
    })
    assert transformer.transform({}) == {'empty': True}


def test_format_no_content_value():
    transformer = Transformer({
        '$': 'format',
        'pattern': '{name}',
        'value': {'$': 'attr', 'name': 'missing'},
    })
    assert transformer.transform({'present': 1}) is None


def test_format_no_content_list_element():
    transformer = Transformer({
        '$': 'format',
        'pattern': '{0}-{1}',
        'value': [
            'a',
            {'$': 'attr', 'name': 'missing'},
        ],
    })
    assert transformer.transform({}) is None


def test_attr_default_parameter():
    transformer = Transformer({
        '$': 'attr',
        'name': 'missing',
        'default': 'fallback',
    })
    assert transformer.transform({'a': 1}) == 'fallback'


def test_get_default_parameter():
    transformer = Transformer({
        '$': 'get',
        'name': 'missing_var',
        'default': 0,
    })
    assert transformer.transform({}) == 0


def test_format_default_parameter():
    transformer = Transformer({
        '$': 'format',
        'pattern': '{name}',
        'value': {'$': 'attr', 'name': 'missing'},
        'default': 'n/a',
    })
    assert transformer.transform({}) == 'n/a'


def test_include_default_parameter():
    def loader(name):
        return Transformer({'$': 'attr', 'name': 'missing'})

    transformer = Transformer(
        {'$': 'include', 'name': 'sub', 'default': 'fallback'},
        template_loader=loader,
    )
    assert transformer.transform({'a': 1}) == 'fallback'
