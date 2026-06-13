from . import base


class FormatSkipsMissingValue(base.TableDataBaseCase):
    """
    Produces no result when a formatted value is missing instead of interpolating
    the sentinel repr into the output string.
    """
    tags = ['format', 'format:value', 'attr']
    template = {
        '$': 'format',
        'pattern': 'Hello, {name}!',
        'value': {'$': 'attr', 'name': 'name'},
    }
    data = {'greeting': 'Hi'}
    result = None
