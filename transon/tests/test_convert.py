from . import base


class ConvertValues(base.TableDataBaseCase):
    """
    Converts input string into integer in base-16.
    """
    tags = ['call:values']
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
    tags = ['call:value', 'expr:value']
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
    tags = ['call']
    template = {
        '$': 'call',
        'name': 'str',
    }
    data = 123
    result = "123"
