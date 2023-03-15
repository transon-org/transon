import operator

from transon import Transformer


Transformer.register_operator('lt')(operator.lt)
Transformer.register_operator('le')(operator.le)
Transformer.register_operator('eq')(operator.eq)
Transformer.register_operator('ne')(operator.ne)
Transformer.register_operator('ge')(operator.ge)
Transformer.register_operator('gt')(operator.gt)

Transformer.register_operator('add')(operator.add)
Transformer.register_operator('sub')(operator.sub)
Transformer.register_operator('mul')(operator.mul)
Transformer.register_operator('div')(operator.truediv)
Transformer.register_operator('mod')(operator.mod)

Transformer.register_operator('and')(operator.and_)
Transformer.register_operator('or')(operator.or_)
Transformer.register_operator('not')(operator.not_)

Transformer.register_operator('<')(operator.lt)
Transformer.register_operator('<=')(operator.le)
Transformer.register_operator('==')(operator.eq)
Transformer.register_operator('!=')(operator.ne)
Transformer.register_operator('>=')(operator.ge)
Transformer.register_operator('>')(operator.gt)

Transformer.register_operator('+')(operator.add)
Transformer.register_operator('-')(operator.sub)
Transformer.register_operator('*')(operator.mul)
Transformer.register_operator('/')(operator.truediv)
Transformer.register_operator('%')(operator.mod)

Transformer.register_operator('&&')(operator.and_)
Transformer.register_operator('||')(operator.or_)
Transformer.register_operator('!')(operator.not_)
