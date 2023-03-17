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


def test_extension():
    class ExtendedTransformer(Transformer):
        pass

    @ExtendedTransformer.register_convertor('xxx')
    def xxx(value):
        return f'-=xxx={value}=xxx=-'

    transformer = Transformer({
        '$': 'convert',
        'name': 'xxx',
    })

    transformer_ex = ExtendedTransformer({
        '$': 'convert',
        'name': 'xxx',
    })

    with pytest.raises(DefinitionError):
        transformer.transform('TRANSON')

    assert transformer_ex.transform('TRANSON') == '-=xxx=TRANSON=xxx=-'
