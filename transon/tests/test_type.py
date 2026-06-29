from . import base


class TypeOfObject(base.TableDataBaseCase):
    """
    Reports the JSON type of an object with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = {'a': 1}
    result = 'object'


class TypeOfArray(base.TableDataBaseCase):
    """
    Reports the JSON type of an array with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = [1, 2, 3]
    result = 'array'


class TypeOfString(base.TableDataBaseCase):
    """
    Reports the JSON type of a string with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = 'hello'
    result = 'string'


class TypeOfInt(base.TableDataBaseCase):
    """
    Reports the JSON type of an integer with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = 7
    result = 'int'


class TypeOfFloat(base.TableDataBaseCase):
    """
    Reports the JSON type of a floating-point number with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = 2.5
    result = 'float'


class TypeOfBoolean(base.TableDataBaseCase):
    """
    Reports the JSON type of a boolean with the `type` function (note booleans are
    distinguished from integers).
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = True
    result = 'boolean'


class TypeOfNull(base.TableDataBaseCase):
    """
    Reports the JSON type of `null` with the `type` function.
    """
    tags = ['call', 'func:type']
    template = {'$': 'call', 'name': 'type'}
    data = None
    result = 'null'


class TypeDispatchWithSwitch(base.TableDataBaseCase):
    """
    Dispatches on a node's JSON type with a non-throwing `switch` whose key is the
    `type` function — the canonical pattern a generated codec uses to walk an
    arbitrary document.
    """
    tags = ['switch', 'switch:key', 'call', 'func:type']
    template = {
        '$': 'switch',
        'key': {'$': 'call', 'name': 'type', 'value': {'$': 'this'}},
        'cases': {
            'object': 'is-object',
            'array': 'is-array',
        },
        'default': 'is-scalar',
    }
    data = [1, 2]
    result = 'is-array'
