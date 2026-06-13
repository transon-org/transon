from . import base


class SetVisibleToLaterSiblingKey(base.TableDataBaseCase):
    """
    A variable stored at one literal-dict key is visible to later sibling keys
    evaluated in the same scope (dict insertion order).
    """
    tags = ['set', 'set:name', 'get', 'get:name']
    template = {
        'first': {'$': 'set', 'name': 'saved'},
        'second': {'$': 'get', 'name': 'saved'},
    }
    data = {'id': 1}
    result = {
        'first': {'id': 1},
        'second': {'id': 1},
    }


class SetInvisibleToEarlierSiblingKey(base.TableDataBaseCase):
    """
    A variable stored at one literal-dict key is not visible to sibling keys
    that were already evaluated — visibility depends on dict key order.
    """
    tags = ['set', 'get']
    template = {
        'second': {'$': 'get', 'name': 'saved', 'default': 'missing'},
        'first': {'$': 'set', 'name': 'saved'},
    }
    data = {'id': 1}
    result = {
        'second': 'missing',
        'first': {'id': 1},
    }


class SetInFirstChainFuncVisibleToSibling(base.TableDataBaseCase):
    """
    The first func of a `chain` runs in the caller's context, so a `set` there
    is visible to later sibling templates outside the `chain`.
    """
    tags = ['chain', 'set', 'get']
    template = {
        'pipeline': {
            '$': 'chain',
            'funcs': [
                {'$': 'set', 'name': 'saved'},
                {'$': 'this'},
            ],
        },
        'later': {'$': 'get', 'name': 'saved'},
    }
    data = {'count': 3}
    result = {
        'pipeline': {'count': 3},
        'later': {'count': 3},
    }


class SetInLaterChainFuncNotVisibleToSibling(base.TableDataBaseCase):
    """
    A `set` in a non-first `chain` func writes to a derived context and is not
    visible to sibling templates outside the `chain`.
    """
    tags = ['chain', 'set', 'get']
    template = {
        'pipeline': {
            '$': 'chain',
            'funcs': [
                {'$': 'this'},
                {'$': 'set', 'name': 'inner'},
            ],
        },
        'later': {'$': 'get', 'name': 'inner', 'default': 'gone'},
    }
    data = 42
    result = {
        'pipeline': 42,
        'later': 'gone',
    }


class SetInFirstChainFuncVisibleToLaterFunc(base.TableDataBaseCase):
    """
    A `set` in the first `chain` func is copied into derived contexts and is
    visible to later funcs in the same `chain`.
    """
    tags = ['chain', 'set', 'get']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'set', 'name': 'saved'},
            {'$': 'get', 'name': 'saved'},
        ],
    }
    data = 'hello'
    result = 'hello'


class SetBeforeMapVisibleInsideIteration(base.TableDataBaseCase):
    """
    A variable stored before a `map` is copied into each iteration context and
    is visible inside the loop.
    """
    tags = ['chain', 'set', 'get', 'map:item']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'set', 'name': 'root'},
            {
                '$': 'map',
                'item': {'$': 'get', 'name': 'root'},
            },
        ],
    }
    data = [1, 2]
    result = [[1, 2], [1, 2]]


class SetInsideMapNotVisibleAfterLoop(base.TableDataBaseCase):
    """
    A variable stored inside a `map` iteration is not visible after the loop
    ends — each iteration uses a derived context.
    """
    tags = ['chain', 'set', 'get', 'map:item']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'map',
                'item': {'$': 'set', 'name': 'item_var'},
            },
            {'$': 'get', 'name': 'item_var', 'default': 'isolated'},
        ],
    }
    data = [1, 2]
    result = 'isolated'
