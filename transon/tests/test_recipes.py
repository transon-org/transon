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
