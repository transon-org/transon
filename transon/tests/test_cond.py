from . import base


class CondFirstTruthyArm(base.TableDataBaseCase):
    """
    Evaluates each arm's `when` in order and emits the `then` of the first truthy
    one. Only the selected `then` is walked; later arms are skipped. This is the
    ordered, multi-way generalization of an `if`/`else` chain.
    """
    tags = ['cond', 'cond:cases', 'cond:default', 'expr', 'expr:value']
    template = {
        '$': 'cond',
        'cases': [
            {'when': {'$': 'expr', 'op': '<', 'value': 0}, 'then': 'negative'},
            {'when': {'$': 'expr', 'op': '==', 'value': 0}, 'then': 'zero'},
        ],
        'default': 'positive',
    }
    data = -5
    result = 'negative'


class CondDefaultBranch(base.TableDataBaseCase):
    """
    Falls back to the `default` template when no arm's `when` is truthy.
    """
    tags = ['cond', 'cond:default', 'expr']
    template = {
        '$': 'cond',
        'cases': [
            {'when': {'$': 'expr', 'op': '<', 'value': 0}, 'then': 'negative'},
            {'when': {'$': 'expr', 'op': '==', 'value': 0}, 'then': 'zero'},
        ],
        'default': 'positive',
    }
    data = 10
    result = 'positive'
