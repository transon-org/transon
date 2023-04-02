from . import base


class NoContentForAttr(base.TableDataBaseCase):
    """
    Gets variable names `foo` that does not exist from context.
    Then tries to get attribute named `bar` of non-existing value.
    This results into no value which translates into `None`.
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
    Creates a dict with item key that has no value.
    It results with empty object.
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
    Creates a dict with item value that has no value.
    It results with empty object.
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
    Demonstrates skipping of items in `list` generation by `map` rule when they have no value.
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
    Demonstrates skipping of items in `dict` generation by `map` rule when they have no value.
    """
    tags = ['map:key', 'map:value', 'get']
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
