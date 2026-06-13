from . import base


class ObjectDynamicKeyValue(base.TableDataBaseCase):
    """
    Builds a single-item dict whose attribute name comes from the input.
    Both the key and the value are dynamic templates.
    """
    tags = ['object', 'object:key', 'object:value', 'attr:name']
    template = {
        '$': 'object',
        'key': {'$': 'attr', 'name': 'field'},
        'value': {'$': 'attr', 'name': 'amount'},
    }
    data = {
        'field': 'price',
        'amount': 42,
    }
    result = {
        'price': 42,
    }


class ObjectFieldsLiteralMarker(base.TableDataBaseCase):
    """
    Produces an object whose key is the marker (`$`) itself.

    In `fields` mode the keys of the mapping are emitted verbatim, so `$` is kept
    as literal data instead of being interpreted as a rule invocation. The values
    are still walked as templates, so the emitted document can mix literal marker
    keys with dynamic values — here transon is used to generate a transon template.
    """
    tags = ['object', 'object:fields', 'attr:name']
    template = {
        '$': 'object',
        'fields': {
            '$': 'attr',
            'name': {'$': 'attr', 'name': 'field'},
        },
    }
    data = {
        'field': 'price',
    }
    result = {
        '$': 'attr',
        'name': 'price',
    }


class ObjectFieldsMultipleLiteralKeys(base.TableDataBaseCase):
    """
    Builds a multi-key object with literal keys and dynamic values.

    This is handy for documents that use `$`-prefixed operator keys (e.g. MongoDB
    queries): the keys stay literal while each value is interpolated from input.
    """
    tags = ['object:fields', 'attr:name']
    template = {
        '$': 'object',
        'fields': {
            '$gt': {'$': 'attr', 'name': 'low'},
            '$lt': {'$': 'attr', 'name': 'high'},
        },
    }
    data = {
        'low': 10,
        'high': 100,
    }
    result = {
        '$gt': 10,
        '$lt': 100,
    }
