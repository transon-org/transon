from . import base


class JoinSkipsMissingStringFields(base.TableDataBaseCase):
    """
    Joins optional string fields, omitting any that are missing.
    """
    tags = ['join', 'attr']
    template = {
        '$': 'join',
        'items': [
            {'$': 'attr', 'name': 'first'},
            {'$': 'attr', 'name': 'middle'},
            {'$': 'attr', 'name': 'last'},
        ],
        'sep': ' ',
    }
    data = {
        'first': 'Ada',
        'last': 'Lovelace',
    }
    result = 'Ada Lovelace'
