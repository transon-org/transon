import pytest

from transon import (
    Transformer,
    DefinitionError,
)


@pytest.mark.parametrize('template', [
    {'$': 'xxx'},
    {'$': 'join'},
    {'$': 'attr'},
    {'$': 'map'},
    {'$': 'zip'},
    {'$': 'expr', 'op': 'xxx'},
    {'$': 'convert', 'name': 'xxx'},
])
def test_invalid_rule(template):
    transformer = Transformer(template)

    with pytest.raises(DefinitionError):
        transformer.transform(0)


def test_get_rules():
    assert {
        rule.__rule_name__
        for rule in Transformer.get_rules()
    } == {
        'this', 'parent', 'item', 'key', 'index', 'value', 'set', 'get',
        'attr', 'object', 'map', 'zip', 'file', 'join', 'chain', 'expr',
        'call', 'format'
    }


def test_extension():
    class ExtendedTransformer(Transformer):
        pass

    @ExtendedTransformer.register_function('xxx')
    def xxx(value):
        return f'-=xxx={value}=xxx=-'

    transformer = Transformer({
        '$': 'call',
        'name': 'xxx',
    })

    transformer_ex = ExtendedTransformer({
        '$': 'call',
        'name': 'xxx',
    })

    with pytest.raises(DefinitionError):
        transformer.transform('TRANSON')

    assert transformer_ex.transform('TRANSON') == '-=xxx=TRANSON=xxx=-'
