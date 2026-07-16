from . import base


class OperatorLessThan(base.TableDataBaseCase):
    """
    `<`/`lt` returns `true` when the current context value is strictly less than the
    given value.
    """
    tags = ['op:lt', 'expr:value']
    template = {
        '$': 'expr',
        'op': '<',
        'value': 10,
    }
    data = 3
    result = True


class OperatorLessOrEqual(base.TableDataBaseCase):
    """
    `<=`/`le` returns `true` when the current context value is less than or equal to the
    given value.
    """
    tags = ['op:le', 'expr:value']
    template = {
        '$': 'expr',
        'op': 'le',
        'value': 10,
    }
    data = 10
    result = True


class OperatorEqual(base.TableDataBaseCase):
    """
    `==`/`eq` returns `true` when both operands are equal.
    """
    tags = ['op:eq', 'expr:value']
    template = {
        '$': 'expr',
        'op': '==',
        'value': 5,
    }
    data = 5
    result = True


class OperatorNotEqual(base.TableDataBaseCase):
    """
    `!=`/`ne` returns `true` when the operands differ.
    """
    tags = ['op:ne', 'expr:value']
    template = {
        '$': 'expr',
        'op': '!=',
        'value': 5,
    }
    data = 6
    result = True


class OperatorGreaterOrEqual(base.TableDataBaseCase):
    """
    `>=`/`ge` returns `true` when the current context value is greater than or equal to
    the given value.
    """
    tags = ['op:ge', 'expr:value']
    template = {
        '$': 'expr',
        'op': 'ge',
        'value': 3,
    }
    data = 10
    result = True


class OperatorGreaterThan(base.TableDataBaseCase):
    """
    `>`/`gt` returns `true` when the current context value is strictly greater than the
    given value.
    """
    tags = ['op:gt', 'expr:value']
    template = {
        '$': 'expr',
        'op': '>',
        'value': 3,
    }
    data = 10
    result = True


class OperatorSubtract(base.TableDataBaseCase):
    """
    `-`/`sub` subtracts the given value from the current context value.
    """
    tags = ['op:sub', 'expr:value']
    template = {
        '$': 'expr',
        'op': '-',
        'value': 4,
    }
    data = 10
    result = 6


class OperatorMultiply(base.TableDataBaseCase):
    """
    `*`/`mul` multiplies the current context value by the given value.
    """
    tags = ['op:mul', 'expr:value']
    template = {
        '$': 'expr',
        'op': '*',
        'value': 7,
    }
    data = 6
    result = 42


class OperatorDivide(base.TableDataBaseCase):
    """
    `/`/`div` performs true division; the result is a float.
    """
    tags = ['op:div', 'expr:value']
    template = {
        '$': 'expr',
        'op': '/',
        'value': 2,
    }
    data = 9
    result = 4.5


class OperatorModulo(base.TableDataBaseCase):
    """
    `%`/`mod` returns the remainder of dividing the current context value by the given
    value.
    """
    tags = ['op:mod', 'expr:value']
    template = {
        '$': 'expr',
        'op': '%',
        'value': 2,
    }
    data = 9
    result = 1


class OperatorInArray(base.TableDataBaseCase):
    """
    `in` returns `true` when the left operand is an element of an array.
    Total — never raises.
    """
    tags = ['op:in', 'expr:value']
    template = {
        '$': 'expr',
        'op': 'in',
        'value': ['a', 'b', 'c'],
    }
    data = 'b'
    result = True


class OperatorInObjectKey(base.TableDataBaseCase):
    """
    `in` returns `true` when the left operand is a key of an object.
    """
    tags = ['op:in', 'expr:value']
    template = {
        '$': 'expr',
        'op': 'in',
        'value': {'name': 'Ada', 'role': 'engineer'},
    }
    data = 'name'
    result = True


class OperatorInString(base.TableDataBaseCase):
    """
    `in` returns `true` when the left operand is a substring of a string.
    """
    tags = ['op:in', 'expr:value']
    template = {
        '$': 'expr',
        'op': 'in',
        'value': 'transon',
    }
    data = 'son'
    result = True
