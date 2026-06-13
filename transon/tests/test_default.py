from . import base


class AttrWithDefault(base.TableDataBaseCase):
    """
    Returns a fallback string when a missing attribute is looked up.
    """
    tags = ['attr', 'attr:default']
    template = {
        '$': 'attr',
        'name': 'nickname',
        'default': 'anonymous',
    }
    data = {'name': 'Alice'}
    result = 'anonymous'


class GetWithDefault(base.TableDataBaseCase):
    """
    Returns a fallback number when an undefined variable is requested.
    """
    tags = ['get', 'get:default']
    template = {
        '$': 'get',
        'name': 'count',
        'default': 0,
    }
    data = {}
    result = 0


class FormatWithDefault(base.TableDataBaseCase):
    """
    Returns a fallback label when a formatted value is missing.
    """
    tags = ['format', 'format:default']
    template = {
        '$': 'format',
        'pattern': '{label}',
        'value': {'$': 'attr', 'name': 'label'},
        'default': 'unknown',
    }
    data = {'other': 1}
    result = 'unknown'
