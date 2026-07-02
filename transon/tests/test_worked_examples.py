from . import base


class WorkedExampleNestedArithmetic(base.TableDataBaseCase):
    """
    **Arithmetic via nested rules — no string DSL.**

    transon has no expression mini-language: you compose arithmetic by *nesting*
    `expr` rules, each one a plain JSON object. Here `(a + b) * c` is built by feeding
    the result of an inner `+` into an outer `*`, with every operand read from the
    input by `attr`. Where JSONata or jq would write a terse `(a + b) * c`, transon
    keeps the expression as data — so it can be stored, generated, diffed, and
    validated like any other JSON.
    """
    tags = ['worked-example']
    template = {
        '$': 'expr',
        'op': '*',
        'values': [
            {
                '$': 'expr',
                'op': '+',
                'values': [
                    {'$': 'attr', 'name': 'a'},
                    {'$': 'attr', 'name': 'b'},
                ],
            },
            {'$': 'attr', 'name': 'c'},
        ],
    }
    data = {'a': 2, 'b': 3, 'c': 4}
    result = 20


class WorkedExampleReshapeRecords(base.TableDataBaseCase):
    """
    **Reshape a list of records (line items → billing summary).**

    The everyday JSON-transformation task — the same shape JSONata demonstrates with
    `Account.Order.Product.(Price * Quantity)` and jq with
    `.items | map({sku, amount: (.qty * .price)})`. `chain` pulls the `items` list out
    of the input with `attr`, then `map` rebuilds each record as a new `object` whose
    `amount` field is computed on the fly by an `expr` multiplication. Five rules —
    `chain` → `attr` → `map` → `object` → `expr` — compose into one declarative
    template, showing how the primitives documented separately below combine into a
    real transformation.
    """
    tags = ['worked-example']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'attr', 'name': 'items'},
            {
                '$': 'map',
                'item': {
                    '$': 'object',
                    'fields': {
                        'sku': {'$': 'attr', 'name': 'sku'},
                        'amount': {
                            '$': 'expr',
                            'op': '*',
                            'values': [
                                {'$': 'attr', 'name': 'qty'},
                                {'$': 'attr', 'name': 'price'},
                            ],
                        },
                    },
                },
            },
        ],
    }
    data = {
        'order_id': 'SO-10428',
        'currency': 'USD',
        'items': [
            {'sku': 'DESK-01', 'name': 'Standing desk', 'qty': 2, 'price': 300},
            {'sku': 'CHAIR-09', 'name': 'Ergonomic chair', 'qty': 4, 'price': 120},
            {'sku': 'LAMP-22', 'name': 'Desk lamp', 'qty': 3, 'price': 45},
            {'sku': 'MON-27', 'name': '27\" monitor', 'qty': 2, 'price': 250},
            {'sku': 'USB-03', 'name': 'USB-C cable', 'qty': 10, 'price': 12},
        ],
    }
    result = [
        {'sku': 'DESK-01', 'amount': 600},
        {'sku': 'CHAIR-09', 'amount': 480},
        {'sku': 'LAMP-22', 'amount': 135},
        {'sku': 'MON-27', 'amount': 500},
        {'sku': 'USB-03', 'amount': 120},
    ]


class WorkedExampleRenameAndFlatten(base.TableDataBaseCase):
    """
    **Rename keys and flatten a nested record.**

    The signature task of structural mappers like Jolt's `shift` spec: take a nested
    document and emit a flat one with renamed keys. `object` in `fields` mode lists the
    output keys literally; each value pulls from the input — `attr` with `names`
    walks a path (`profile → firstName`) to flatten, and `format` joins first/last into
    a single `fullName` (the equivalent of JSONata's `firstName & " " & lastName`).
    """
    tags = ['worked-example']
    template = {
        '$': 'object',
        'fields': {
            'userId': {'$': 'attr', 'name': 'id'},
            'fullName': {
                '$': 'format',
                'pattern': '{} {}',
                'value': [
                    {'$': 'attr', 'names': ['profile', 'firstName']},
                    {'$': 'attr', 'names': ['profile', 'lastName']},
                ],
            },
            'email': {'$': 'attr', 'name': 'email'},
        },
    }
    data = {
        'id': 7,
        'profile': {'firstName': 'Ada', 'lastName': 'Lovelace'},
        'email': 'ada@example.com',
    }
    result = {
        'userId': 7,
        'fullName': 'Ada Lovelace',
        'email': 'ada@example.com',
    }


class WorkedExampleFilterAndProject(base.TableDataBaseCase):
    """
    **Filter a list, then project a field.**

    The classic select-and-pluck pipeline: JSONata writes `users[active].name`, jq
    writes `map(select(.active)) | map(.name)`. transon composes it from two rules in a
    `chain` — `filter` keeps the records whose `active` flag is truthy, then `map`
    projects each survivor down to its `name`, dropping the other fields.
    """
    tags = ['worked-example']
    template = {
        '$': 'chain',
        'funcs': [
            {'$': 'filter', 'cond': {'$': 'attr', 'name': 'active'}},
            {'$': 'map', 'item': {'$': 'attr', 'name': 'name'}},
        ],
    }
    data = [
        {'id': 1, 'name': 'Ada Lovelace', 'role': 'admin', 'active': True},
        {'id': 2, 'name': 'Alan Turing', 'role': 'editor', 'active': False},
        {'id': 3, 'name': 'Grace Hopper', 'role': 'admin', 'active': True},
        {'id': 4, 'name': 'Edsger Dijkstra', 'role': 'viewer', 'active': False},
        {'id': 5, 'name': 'Katherine Johnson', 'role': 'editor', 'active': True},
        {'id': 6, 'name': 'Margaret Hamilton', 'role': 'admin', 'active': True},
    ]
    result = ['Ada Lovelace', 'Grace Hopper', 'Katherine Johnson', 'Margaret Hamilton']


class WorkedExampleIndexByKey(base.TableDataBaseCase):
    """
    **Index a list into a lookup dict (key-by).**

    Turning a list of records into a dict keyed by one of their fields — jq's
    `INDEX(.code)`, lodash's `keyBy` — is a staple of data shaping. `map` in its
    `key`/`value` mode builds the dict directly: `attr` picks the `code` for each
    key and the `name` for each value, collapsing the list (and discarding the other
    fields) into an O(1) lookup table.
    """
    tags = ['worked-example']
    template = {
        '$': 'map',
        'key': {'$': 'attr', 'name': 'code'},
        'value': {'$': 'attr', 'name': 'name'},
    }
    data = [
        {'code': 'US', 'name': 'United States', 'capital': 'Washington, D.C.'},
        {'code': 'FR', 'name': 'France', 'capital': 'Paris'},
        {'code': 'JP', 'name': 'Japan', 'capital': 'Tokyo'},
        {'code': 'BR', 'name': 'Brazil', 'capital': 'Brasilia'},
        {'code': 'KE', 'name': 'Kenya', 'capital': 'Nairobi'},
        {'code': 'DE', 'name': 'Germany', 'capital': 'Berlin'},
    ]
    result = {
        'US': 'United States',
        'FR': 'France',
        'JP': 'Japan',
        'BR': 'Brazil',
        'KE': 'Kenya',
        'DE': 'Germany',
    }


class WorkedExampleOptionalFieldsAndDefaults(base.TableDataBaseCase):
    """
    **Optional fields and defaults (the `NO_CONTENT` model).**

    Conditionally including a field is awkward in many tools (JSON-e reaches for
    `$if`, Jolt for cardinality tricks). In transon it falls out of the data model:
    a value that resolves to *no value* is simply skipped. Here `phone` is absent from
    the input, so `attr` yields `NO_CONTENT` and `object` omits the key entirely;
    meanwhile `tier` is missing too but supplies a `default`, so it lands as `"free"`.
    One uniform rule — skip *no value*, fall back on `default` — covers both
    "drop when absent" and "substitute when absent".
    """
    tags = ['worked-example']
    template = {
        '$': 'object',
        'fields': {
            'name': {'$': 'attr', 'name': 'name'},
            'email': {'$': 'attr', 'name': 'email'},
            'tier': {'$': 'attr', 'name': 'tier', 'default': 'free'},
            'phone': {'$': 'attr', 'name': 'phone'},
        },
    }
    data = {
        'name': 'Ada',
        'email': 'ada@example.com',
    }
    result = {
        'name': 'Ada',
        'email': 'ada@example.com',
        'tier': 'free',
    }


class WorkedExampleConditionalEnrichmentInsideMap(base.TableDataBaseCase):
    """
    **Conditional enrichment inside a map (per-record branch logic).**

    *The shape most real templates take*: iterate a list of records and rebuild
    each one with fields that depend on the record's own values. `map` drives the
    iteration and `object` shapes each output record; inside it, `switch`
    dispatches a short plan code to its display label (with a `default` for
    unknown codes), while `cond` buckets the numeric `seats` field with an `expr`
    comparison. Only the selected branch of each dispatch is ever evaluated —
    where JSONata would write nested ternaries and jq an `if/elif` chain, transon
    keeps every branch a plain JSON template.
    """
    tags = ['worked-example']
    template = {
        '$': 'map',
        'item': {
            '$': 'object',
            'fields': {
                'name': {'$': 'attr', 'name': 'name'},
                'plan': {
                    '$': 'switch',
                    'key': {'$': 'attr', 'name': 'plan'},
                    'cases': {
                        'pro': 'Professional',
                        'ent': 'Enterprise',
                    },
                    'default': 'Free',
                },
                'size': {
                    '$': 'chain',
                    'funcs': [
                        {'$': 'attr', 'name': 'seats'},
                        {
                            '$': 'cond',
                            'cases': [
                                {
                                    'when': {'$': 'expr', 'op': '<', 'value': 10},
                                    'then': 'small',
                                },
                            ],
                            'default': 'large',
                        },
                    ],
                },
            },
        },
    }
    data = [
        {'name': 'Initech', 'plan': 'ent', 'seats': 250},
        {'name': 'Hooli', 'plan': 'pro', 'seats': 8},
        {'name': 'Pied Piper', 'plan': 'trial', 'seats': 3},
    ]
    result = [
        {'name': 'Initech', 'plan': 'Enterprise', 'size': 'large'},
        {'name': 'Hooli', 'plan': 'Professional', 'size': 'small'},
        {'name': 'Pied Piper', 'plan': 'Free', 'size': 'small'},
    ]
