from . import base


class ExprSimpleMonads1(base.TableDataBaseCase):
    """
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
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
    TODO: Describe
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


class ExprUnary1(base.TableDataBaseCase):
    """
    TODO: Describe
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
    TODO: Describe
    """
    tags = ['expr:op']
    template = {
        '$': 'expr',
        'op': 'not',
    }
    data = False
    result = True
