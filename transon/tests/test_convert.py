from . import base


class ConvertValues(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['convert:values']
    template = {
        '$': 'convert',
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
    TODO: Describe
    """
    tags = ['convert:value']
    template = {
        '$': 'convert',
        'name': 'str',
        'value': {'$': 'this'}
    }
    data = 123
    result = "123"


class ConvertNoParameters(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['convert']
    template = {
        '$': 'convert',
        'name': 'str',
    }
    data = 123
    result = "123"
