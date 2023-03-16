from transon import (
    Transformer,
)


Transformer.register_convertor('str')(str)
Transformer.register_convertor('number')(float)
