from transon import (
    Transformer,
)


Transformer.register_function('str')(str)
Transformer.register_function('int')(int)
Transformer.register_function('float')(float)
