from . import base


class SwitchDispatchOnKey(base.TableDataBaseCase):
    """
    Dispatches on a value read from the input and emits the matching case. Only the
    selected case template is evaluated — the other arms are never walked — so
    `switch` is the lazy alternative to building a dict and indexing it.
    """
    tags = ['switch', 'switch:key', 'switch:cases', 'attr', 'attr:name']
    template = {
        '$': 'switch',
        'key': {'$': 'attr', 'name': 'kind'},
        'cases': {
            'a': 'Apple',
            'b': 'Banana',
        },
    }
    data = {'kind': 'b'}
    result = 'Banana'


class SwitchDefaultBranch(base.TableDataBaseCase):
    """
    Falls back to the `default` template when no case matches the dispatch key
    (this also covers the case where the key evaluates to no value).
    """
    tags = ['switch', 'switch:default']
    template = {
        '$': 'switch',
        'key': {'$': 'attr', 'name': 'kind'},
        'cases': {
            'a': 'Apple',
        },
        'default': 'Unknown',
    }
    data = {'kind': 'z'}
    result = 'Unknown'
