from . import base


class ConvertValues(base.TableDataBaseCase):
    """
    TODO: Describe
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
    TODO: Describe
    """
    tags = ['call:value']
    template = {
        '$': 'call',
        'name': 'str',
        'value': {'$': 'this'}
    }
    data = 123
    result = "123"


class ConvertNoParameters(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['call']
    template = {
        '$': 'call',
        'name': 'str',
    }
    data = 123
    result = "123"
