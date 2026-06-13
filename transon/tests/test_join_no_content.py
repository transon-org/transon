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


class JoinEmptyReturnsNoContent(base.TableDataBaseCase):
    """
    Joining an empty list of items produces no value (`NO_CONTENT`).
    """
    tags = ['join']
    template = {
        '$': 'join',
        'items': [],
    }
    data = {}
    result = None


class JoinEmptyWithDefaultDict(base.TableDataBaseCase):
    """
    When there are no items to join, `default` supplies the result value.
    """
    tags = ['join', 'join:default']
    template = {
        '$': 'join',
        'items': [],
        'default': {},
    }
    data = {}
    result = {}
