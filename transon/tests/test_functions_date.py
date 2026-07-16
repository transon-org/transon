from . import base


class FromEpochIso(base.TableDataBaseCase):
    """
    Converts epoch seconds to a fixed ISO-8601 UTC timestamp with `from_epoch`.
    """
    tags = ['call', 'func:from_epoch']
    template = {'$': 'call', 'name': 'from_epoch'}
    data = 1712345678
    result = '2024-04-05T19:34:38Z'


class FromEpochCustomFormat(base.TableDataBaseCase):
    """
    Formats epoch seconds with an explicit whitelist format via `from_epoch`.
    """
    tags = ['call:values', 'func:from_epoch']
    template = {
        '$': 'call',
        'name': 'from_epoch',
        'values': [{'$': 'this'}, '%Y-%m-%d'],
    }
    data = 1712345678
    result = '2024-04-05'


class ToEpochIso(base.TableDataBaseCase):
    """
    Parses a fixed ISO-8601 UTC timestamp to epoch seconds with `to_epoch`.
    """
    tags = ['call:values', 'func:to_epoch']
    template = {
        '$': 'call',
        'name': 'to_epoch',
        'values': [{'$': 'this'}],
    }
    data = '2024-04-05T19:34:38Z'
    result = 1712345678


class ToEpochCustomFormat(base.TableDataBaseCase):
    """
    Parses a custom-format UTC date string to epoch seconds with `to_epoch`.
    """
    tags = ['call:values', 'func:to_epoch']
    template = {
        '$': 'call',
        'name': 'to_epoch',
        'values': [{'$': 'this'}, '%Y-%m-%dT%H:%M:%S'],
    }
    data = '2024-04-05T19:34:38'
    result = 1712345678
