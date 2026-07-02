from . import base


class RecipeReadNestedValue(base.TableDataBaseCase):
    """
    **Read a deeply nested value.**

    *Task: "I have a value buried under several keys — how do I pull it out?"*

    Give `attr` a `names` path instead of a single `name` and it walks the keys in
    order, returning the value at the end (or *no value* if any segment is missing).
    """
    tags = ['recipe']
    template = {'$': 'attr', 'names': ['address', 'city']}
    data = {
        'name': 'Ada',
        'address': {'city': 'London', 'zip': 'EC1A 1BB'},
    }
    result = 'London'


class RecipeDefaultForMissingField(base.TableDataBaseCase):
    """
    **Fall back to a default when a field is missing.**

    *Task: "How do I substitute a value when the input doesn't have the key?"*

    `attr` returns *no value* for a missing key; add a `default` template and that
    value is used instead. The same `default` parameter exists on `get`, `format`,
    `join`, and `include`.
    """
    tags = ['recipe']
    template = {'$': 'attr', 'name': 'currency', 'default': 'USD'}
    data = {'amount': 42}
    result = 'USD'


class RecipePluckFieldFromEach(base.TableDataBaseCase):
    """
    **Pull one field out of every item (project a list).**

    *Task: "How do I turn a list of records into a list of just one of their
    fields?"*

    `map` in `item` mode rebuilds each element; here the new element is just the
    record's `email`, read by `attr`. The other fields are dropped.
    """
    tags = ['recipe']
    template = {'$': 'map', 'item': {'$': 'attr', 'name': 'email'}}
    data = [
        {'name': 'Ada', 'email': 'ada@example.com'},
        {'name': 'Alan', 'email': 'alan@example.com'},
        {'name': 'Grace', 'email': 'grace@example.com'},
    ]
    result = ['ada@example.com', 'alan@example.com', 'grace@example.com']


class RecipeSwapKeysAndValues(base.TableDataBaseCase):
    """
    **Swap the keys and values of a dict.**

    *Task: "How do I invert a mapping so the values become the keys?"*

    Iterating a dict, `map` exposes each entry through the `key` and `value`
    accessor rules. Building the result in `key`/`value` mode with them crossed over
    inverts the mapping.
    """
    tags = ['recipe']
    template = {
        '$': 'map',
        'key': {'$': 'value'},
        'value': {'$': 'key'},
    }
    data = {'GB': 'United Kingdom', 'FR': 'France', 'JP': 'Japan'}
    result = {'United Kingdom': 'GB', 'France': 'FR', 'Japan': 'JP'}


class RecipeJoinListToString(base.TableDataBaseCase):
    """
    **Join a list of strings into one string.**

    *Task: "How do I concatenate a list into a single delimited string?"*

    `join` concatenates its `items`; when they are all strings it inserts the `sep`
    between them. Here `this` feeds the whole input list straight in.
    """
    tags = ['recipe']
    template = {'$': 'join', 'items': {'$': 'this'}, 'sep': ', '}
    data = ['red', 'green', 'blue']
    result = 'red, green, blue'


class RecipeBuildStringFromFields(base.TableDataBaseCase):
    """
    **Build a string from a record's fields.**

    *Task: "How do I interpolate fields into a template string?"*

    `format` runs Python's `str.format`; when the value is a dict it is unpacked, so
    the pattern can reference fields by name (`{first}`, `{last}`).
    """
    tags = ['recipe']
    template = {'$': 'format', 'pattern': '{first} {last}'}
    data = {'first': 'Ada', 'last': 'Lovelace'}
    result = 'Ada Lovelace'


class RecipeConvertType(base.TableDataBaseCase):
    """
    **Convert a value to a different type.**

    *Task: "My number arrived as a string — how do I parse it?"*

    `call` invokes a registered conversion function (`str`, `int`, `float`) on its
    `value`; here `int` parses the `"42"` read by `attr` into the number `42`.
    """
    tags = ['recipe']
    template = {
        '$': 'call',
        'name': 'int',
        'value': {'$': 'attr', 'name': 'age'},
    }
    data = {'age': '42'}
    result = 42


class RecipeMapCodeToLabel(base.TableDataBaseCase):
    """
    **Map a code to a display label.**

    *Task: "My input has a short status code — how do I turn it into a
    human-readable string?"*

    `switch` compares its evaluated `key` against the literal keys of `cases` and
    returns the matching template's value; only the selected case is evaluated.
    An unknown code falls through to `default`.
    """
    tags = ['recipe']
    template = {
        '$': 'switch',
        'key': {'$': 'attr', 'name': 'status'},
        'cases': {
            'A': 'Active',
            'S': 'Suspended',
            'D': 'Deleted',
        },
        'default': 'Unknown',
    }
    data = {'status': 'S'}
    result = 'Suspended'


class RecipeBucketValueByRanges(base.TableDataBaseCase):
    """
    **Bucket a value by ranges.**

    *Task: "How do I classify a number into small/medium/large?"*

    `cond` evaluates its arms in order and selects the first whose `when` is
    truthy. Each `when` here is an `expr` comparison against the piped value
    (`chain` puts the number into the current context first); values matching
    no arm fall through to `default`.
    """
    tags = ['recipe']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'attr', 'name': 'size'},
            {
                '$': 'cond',
                'cases': [
                    {'when': {'$': 'expr', 'op': '<', 'value': 10}, 'then': 'small'},
                    {'when': {'$': 'expr', 'op': '<', 'value': 100}, 'then': 'medium'},
                ],
                'default': 'large',
            },
        ],
    }
    data = {'size': 42}
    result = 'medium'


class RecipeComputeOnceUseTwice(base.TableDataBaseCase):
    """
    **Compute a value once, use it twice.**

    *Task: "How do I avoid repeating the same calculation in two output fields?"*

    `set` stores the current context value under a variable name (and passes it
    through unchanged), so a `chain` can compute a derived value, store it, and
    let later steps read it back with `get` as many times as needed.
    """
    tags = ['recipe']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'expr',
                'op': '*',
                'values': [
                    {'$': 'attr', 'name': 'qty'},
                    {'$': 'attr', 'name': 'price'},
                ],
            },
            {'$': 'set', 'name': 'total'},
            {
                '$': 'object',
                'fields': {
                    'total': {'$': 'get', 'name': 'total'},
                    'label': {
                        '$': 'format',
                        'pattern': 'Total: {}',
                        'value': {'$': 'get', 'name': 'total'},
                    },
                },
            },
        ],
    }
    data = {'qty': 4, 'price': 25}
    result = {'total': 100, 'label': 'Total: 100'}


class RecipePairUpTwoLists(base.TableDataBaseCase):
    """
    **Pair up two parallel lists into records.**

    *Task: "I have matching lists of names and scores — how do I merge them into
    a list of objects?"*

    `zip` transposes the two lists into `[name, score]` pairs; `map` then rebuilds
    each pair as an `object`, with `attr` reading list items by numeric index.
    """
    tags = ['recipe']
    template = {
        '$': 'chain',
        'funcs': [
            {
                '$': 'zip',
                'items': [
                    {'$': 'attr', 'name': 'names'},
                    {'$': 'attr', 'name': 'scores'},
                ],
            },
            {
                '$': 'map',
                'item': {
                    '$': 'object',
                    'fields': {
                        'name': {'$': 'attr', 'name': 0},
                        'score': {'$': 'attr', 'name': 1},
                    },
                },
            },
        ],
    }
    data = {
        'names': ['Ada', 'Alan', 'Grace'],
        'scores': [95, 88, 97],
    }
    result = [
        {'name': 'Ada', 'score': 95},
        {'name': 'Alan', 'score': 88},
        {'name': 'Grace', 'score': 97},
    ]


class RecipeKeepItemsMatchingCondition(base.TableDataBaseCase):
    """
    **Keep only the items matching a condition.**

    *Task: "How do I filter a list on a comparison, not just a truthy flag?"*

    `filter` keeps the items whose `cond` is truthy; the condition here is an
    `expr` comparison (`price >= 100`) built from the item's own fields, so any
    predicate expressible with operators works — not only boolean flags.
    """
    tags = ['recipe']
    template = {
        '$': 'filter',
        'cond': {
            '$': 'expr',
            'op': '>=',
            'values': [
                {'$': 'attr', 'name': 'price'},
                100,
            ],
        },
    }
    data = [
        {'sku': 'DESK-01', 'price': 300},
        {'sku': 'USB-03', 'price': 12},
        {'sku': 'CHAIR-09', 'price': 120},
        {'sku': 'LAMP-22', 'price': 45},
    ]
    result = [
        {'sku': 'DESK-01', 'price': 300},
        {'sku': 'CHAIR-09', 'price': 120},
    ]
