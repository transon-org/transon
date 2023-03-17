from transon import (
    Transformer,
)


Transformer.register_convertor('str')(str)
Transformer.register_convertor('int')(int)
Transformer.register_convertor('float')(float)
