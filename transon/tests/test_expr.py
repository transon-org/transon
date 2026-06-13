from . import base


class ExprSimpleMonads1(base.TableDataBaseCase):
    """
    Adds suffix to input string.
    Illustrates functionality of `expr` rule in form of monad.
    """
    tags = ['expr:value']
    template = {
        '$': 'expr',
        'op': '+',
        'value': '_suffix',
    }
    data = 'value'
    result = 'value_suffix'


class ExprSimpleMonads2(base.TableDataBaseCase):
    """
    Adds prefix to input string.
    Illustrates functionality of `expr` rule in form of monad and usage of `parent` rule.
    """
    tags = ['chain', 'expr:value', 'parent']
    template = {
        '$': 'chain',
        'funcs': [
            "prefix_",
            {
                '$': 'expr',
                'op': '+',
                'value': {'$': 'parent'},
            }
        ]
    }
    data = 'value'
    result = 'prefix_value'


class ExprMonadsComplex(base.TableDataBaseCase):
    """
    For input dictionary containing two integers returns sum of squares.
    Illustrates functionality of `expr` rule in form of monad.
    """
    tags = ['chain', 'expr:value', 'parent']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'chain',
                'funcs': [
                    {'$': 'attr', 'name': 'a'},
                    {
                        '$': 'expr',
                        'op': '*',
                        'value': {'$': 'this'},
                    }
                ]
            },
            {
                '$': 'expr',
                'op': '+',
                'value': {
                    '$': 'chain',
                    'funcs': [
                        {'$': 'parent'},
                        {'$': 'attr', 'name': 'b'},
                        {
                            '$': 'expr',
                            'op': '*',
                            'value': {'$': 'this'},
                        }
                    ]
                },
            }
        ]
    }
    data = {
        'a': 3,
        'b': 4,
    }
    result = 25


class ExprSimpleValues1(base.TableDataBaseCase):
    """
    Adds suffix to input string.
    Illustrates functionality of `expr` rule with direct parameters.
    """
    tags = ['expr:values', 'this']
    template = {
        '$': 'expr',
        'op': '+',
        'values': [
            {'$': 'this'},
            '_suffix',
        ]
    }
    data = 'value'
    result = 'value_suffix'


class ExprSimpleValues2(base.TableDataBaseCase):
    """
    Adds prefix to input string.
    Illustrates functionality of `expr` rule with direct parameters.
    """
    tags = ['expr:values', 'this']
    template = {
        '$': 'expr',
        'op': '+',
        'values': [
            "prefix_",
            {'$': 'this'},
        ]
    }
    data = 'value'
    result = 'prefix_value'


class ExprValuesComplex(base.TableDataBaseCase):
    """
    For input dictionary containing two integers returns sum of squares.
    Illustrates functionality of `expr` rule with direct parameters.
    """
    tags = ['expr:values']
    template = {
        '$': 'expr',
        'op': '+',
        'values': [
            {
                '$': 'expr',
                'op': '*',
                'values': [
                    {'$': 'attr', 'name': 'a'},
                    {'$': 'attr', 'name': 'a'},
                ]
            },
            {
                '$': 'expr',
                'op': '*',
                'values': [
                    {'$': 'attr', 'name': 'b'},
                    {'$': 'attr', 'name': 'b'},
                ]
            },
        ]
    }
    data = {
        'a': 3,
        'b': 4,
    }
    result = 25


class ExprValuesIgnoresThis(base.TableDataBaseCase):
    """
    With `values`, the operator runs as `reduce(op, evaluated_list)` — the current
    context value is not an implicit argument. Input data affects the result only
    when you reference it explicitly inside a list item (e.g. `{"$": "this"}`).
    """
    tags = ['expr:values']
    template = {
        '$': 'expr',
        'op': '+',
        'values': [1, 2, 3],
    }
    data = 'ignored by values mode'
    result = 6


class ExprLogicalAnd(base.TableDataBaseCase):
    """
    `and`/`&&` use Python logical conjunction (truthiness), not bitwise `&`.
    With integers, `6 and 3` yields `3`, not `2`.
    """
    tags = ['expr:op']
    template = {
        '$': 'expr',
        'op': 'and',
        'value': 3,
    }
    data = 6
    result = 3


class ExprLogicalOr(base.TableDataBaseCase):
    """
    `or`/`||` use Python logical disjunction (truthiness), not bitwise `|`.
    Returns the first truthy operand or the last operand.
    """
    tags = ['expr:op']
    template = {
        '$': 'expr',
        'op': 'or',
        'value': 5,
    }
    data = 0
    result = 5


class ExprUnary1(base.TableDataBaseCase):
    """
    Calculates negation of input using `expr` rule with unary operator as monad.
    """
    tags = ['expr:op']
    template = {
        '$': 'expr',
        'op': '!',
    }
    data = True
    result = False


class ExprUnary2(base.TableDataBaseCase):
    """
    Calculates negation of input using `expr` rule with unary operator in alternative form.
    """
    tags = ['expr:op']
    template = {
        '$': 'expr',
        'op': 'not',
    }
    data = False
    result = True
