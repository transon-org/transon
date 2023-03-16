from transon import (
    Transformer,
)


def lzip(*args):
    return list(zip(*args))


Transformer.register_convertor('str')(str)
Transformer.register_convertor('number')(float)
Transformer.register_convertor('zip')(lzip)
