from . import base


class NoContentForAttr(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['attr:name', 'chain', 'get']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'get', 'name': 'foo'},
            {'$': 'attr', 'name': 'bar'},
        ]
    }
    data = 'value'
    result = None


class NoContentForObjectKey(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['object:key', 'get']
    template = {
        '$': 'object',
        'key': {'$': 'get', 'name': 'foo'},
        'value': 'bar',
    }
    data = 'value'
    result = {}


class NoContentForObjectValue(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['object:value', 'get']
    template = {
        '$': 'object',
        'key': 'foo',
        'value': {'$': 'get', 'name': 'bar'},
    }
    data = 'value'
    result = {}


class NoContentForMappingList(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['map:items', 'get', 'index', 'item']
    template = {
        '$': 'chain',
        'funcs': [
            [
                {'$': 'attr', 'name': 'x'},
                {'$': 'get', 'name': 'nope'},
                {'$': 'attr', 'name': 'y'},
            ],
            {
                '$': 'map',
                'items': [
                    {'$': 'index'},
                    {'$': 'item'},
                ]
            }
        ],
    }
    data = {
        'x': 'xxx',
        'y': 'yyy',
    }
    result = [0, 'xxx', 1, 2, 'yyy']


class NoContentForMappingDict(base.TableDataBaseCase):
    """
    TODO: Describe
    """
    tags = ['map:items', 'get', 'index', 'item']
    template = {
        '$': 'chain',
        'funcs': [
            [
                {
                    'key': {'$': 'attr', 'name': 'x'},
                    'value': {'$': 'get', 'name': 'nope'},
                },
                {
                    'key': {'$': 'get', 'name': 'nope'},
                    'value': {'$': 'attr', 'name': 'y'},
                },
                {
                    'key': {'$': 'attr', 'name': 'x'},
                    'value': {'$': 'attr', 'name': 'y'},
                },
            ],
            {
                '$': 'map',
                'key': {'$': 'attr', 'name': 'key'},
                'value': {'$': 'attr', 'name': 'value'},
            }
        ],
    }
    data = {
        'x': 'xxx',
        'y': 'yyy',
    }
    result = {
        'xxx': 'yyy'
    }
