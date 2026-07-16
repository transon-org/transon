import operator

from transon import Transformer


def _logical_and(a, b):
    return a and b


def _logical_or(a, b):
    return a or b


Transformer.register_operator(
    '<', 'lt', kind='binary', types='any', result='boolean',
    doc='Less-than comparison: `true` when the left operand is strictly less than the right.',
)(operator.lt)
Transformer.register_operator(
    '<=', 'le', kind='binary', types='any', result='boolean',
    doc='Less-than-or-equal comparison.',
)(operator.le)
Transformer.register_operator(
    '==', 'eq', kind='binary', types='any', result='boolean',
    doc='Equality comparison: `true` when both operands are equal.',
)(operator.eq)
Transformer.register_operator(
    '!=', 'ne', kind='binary', types='any', result='boolean',
    doc='Inequality comparison: `true` when the operands differ.',
)(operator.ne)
Transformer.register_operator(
    '>=', 'ge', kind='binary', types='any', result='boolean',
    doc='Greater-than-or-equal comparison.',
)(operator.ge)
Transformer.register_operator(
    '>', 'gt', kind='binary', types='any', result='boolean',
    doc='Greater-than comparison.',
)(operator.gt)

Transformer.register_operator(
    '+', 'add', kind='binary', types='string, number', result='string, number',
    doc='Addition for numbers, concatenation for strings.',
)(operator.add)
Transformer.register_operator(
    '-', 'sub', kind='binary', types='number', result='number',
    doc='Subtraction.',
)(operator.sub)
Transformer.register_operator(
    '*', 'mul', kind='binary', types='number', result='number',
    doc='Multiplication.',
)(operator.mul)
Transformer.register_operator(
    '/', 'div', kind='binary', types='number', result='number',
    doc='True division; the result is a float.',
)(operator.truediv)
Transformer.register_operator(
    '%', 'mod', kind='binary', types='number', result='number',
    doc='Modulo: the remainder of a division.',
)(operator.mod)

Transformer.register_operator(
    '&&', 'and', kind='binary', types='any', result='any',
    doc='Logical conjunction by truthiness (Python `and`). Returns one of the operands, '
        'not a strict boolean.',
)(_logical_and)
Transformer.register_operator(
    '||', 'or', kind='binary', types='any', result='any',
    doc='Logical disjunction by truthiness (Python `or`). Returns the first truthy '
        'operand and treats `NO_CONTENT` as falsy.',
)(_logical_or)
Transformer.register_operator(
    '!', 'not', kind='unary', types='boolean', result='boolean',
    doc='Logical negation (Python `not`).',
)(operator.not_)


def _in(a, b):
    """Total membership: is ``a`` a member of ``b``? Never raises."""
    if isinstance(b, list):
        return a in b
    if isinstance(b, str):
        return isinstance(a, str) and a in b
    if isinstance(b, dict):
        return isinstance(a, str) and a in b
    return False


Transformer.register_operator(
    'in', 'in', kind='binary', types='any', result='boolean',
    doc='Membership: `true` when the left operand is a member of the right. '
        'Array → element membership; string → substring (left must be a string, '
        'else `false`); object → key presence (left must be a string, else `false`); '
        'any other container → `false`. Total — never raises.',
)(_in)
