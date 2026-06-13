from . import base


class LookupMissingAttr(base.TableDataBaseCase):
    """
    Returns no result when a named attribute is absent from the input.
    Used as an included sub-template in ``IncludeWithDefault``.
    """
    tags = ['attr']
    template = {'$': 'attr', 'name': 'missing'}
    data = {}
    result = None


class IncludeWithDefault(base.TableDataBaseCase):
    """
    Returns a fallback when the included template produces no result.
    """
    tags = ['include', 'include:default']
    template = {
        '$': 'include',
        'name': 'LookupMissingAttr',
        'default': 'fallback',
    }
    data = {}
    result = 'fallback'


class Include(base.TableDataBaseCase):
    """
    Illustrates usage of `include` rule by iterating over input `list` and applying different template to each item.
    Produces a `list` of results applying `MapListsToDict` template.
    For all examples in this documentation you can use them under their name in include command.
    This was achieved by providing special `template_loader` factory to `Transformer` class.
    """
    tags = ['include', 'include:name']
    template = {
        '$': 'map',
        'item': {
            '$': 'include',
            'name': 'MapListsToDict',
        },
    }
    data = [
        {
            'keys': ['a', 'b', 'c'],
            'values': [1, 2, 3],
        },
        {
            'keys': ['d', 'e', 'f'],
            'values': [4, 5, 6],
        },
    ]
    result = [
        {
            'a': 1,
            'b': 2,
            'c': 3,
        },
        {
            'd': 4,
            'e': 5,
            'f': 6,
        }
    ]
