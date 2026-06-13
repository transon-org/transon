from . import base


class ConvertValues(base.TableDataBaseCase):
    """
    Converts input string into integer in base-16.
    """
    tags = ['call:values', 'func:int']
    template = {
        '$': 'call',
        'name': 'int',
        'values': [
            {'$': 'this'},
            16
        ]
    }
    data = "FF"
    result = 255


class ConvertValue(base.TableDataBaseCase):
    """
    Adds 100 to input integer and converts result into string.
    Illustrates usage of `call` attribute `value`.
    """
    tags = ['call:value', 'expr:value', 'op:add', 'func:str']
    template = {
        '$': 'call',
        'name': 'str',
        'value': {
            '$': 'expr',
            'op': 'add',
            'value': 100,
        }
    }
    data = 123
    result = "223"


class ConvertNoParameters(base.TableDataBaseCase):
    """
    Converts input integer into string.
    """
    tags = ['call', 'call:name', 'func:str']
    template = {
        '$': 'call',
        'name': 'str',
    }
    data = 123
    result = "123"


class ConvertToFloat(base.TableDataBaseCase):
    """
    Parses an input string into a floating-point number using the `float` function.
    """
    tags = ['call', 'func:float']
    template = {
        '$': 'call',
        'name': 'float',
    }
    data = "2.5"
    result = 2.5
