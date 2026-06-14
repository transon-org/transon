from . import base


class ErrorInvalidRuleName(base.ErrorBaseCase):
    """
    **`DefinitionError` — unknown rule.**

    A dict whose marker (`$`) names a rule transon doesn't know is a malformed
    template, so the engine raises `DefinitionError` *before* touching the data. The
    message names the offending rule and pins the location: ``at template → nope``
    points straight at the bad node.
    """
    tags = ['error']
    error_type = 'DefinitionError'
    template = {'$': 'nope'}
    data = {}
    error = (
        'Invalid rule `nope`\n'
        '  at template → nope'
    )


class ErrorMissingRequiredAttr(base.ErrorBaseCase):
    """
    **`DefinitionError` — missing a required parameter.**

    The `attr` rule needs either `name` or `names` to know what to read. Omitting both
    is a template mistake, not a data problem, so it surfaces as a `DefinitionError`.
    The located message tells you both *what* is missing and *where*
    (``at template → attr``).
    """
    tags = ['error']
    error_type = 'DefinitionError'
    template = {'$': 'attr'}
    data = {'name': 'Ada'}
    error = (
        'either `name` or `names` attribute is required for `attr` rule\n'
        '  at template → attr'
    )


class ErrorAccessorOutsideScope(base.ErrorBaseCase):
    """
    **`DefinitionError` — iteration accessor used out of scope.**

    The `item` accessor only has meaning inside a `map`/`filter` iteration. Used at the
    top level it has nothing to refer to, so the engine reports a `DefinitionError`
    explaining the valid scope — again with the ``at template → item`` location so you
    can find the stray accessor.
    """
    tags = ['error']
    error_type = 'DefinitionError'
    template = {'$': 'item'}
    data = [1, 2, 3]
    error = (
        '`item` is only valid inside `map`/`filter` over a list\n'
        '  at template → item'
    )


class ErrorUnknownParamOnValidate(base.ErrorBaseCase):
    """
    **`DefinitionError` — caught by static validation (no data needed).**

    `Transformer(template, validate=True)` (or calling `.validate()`) checks the
    template's structure up front. Here a typo — `nmae` instead of `name` — is flagged
    without ever running a transform, and the location walks into the nested node:
    ``at template → greeting → attr``. This is the same error class `transform` would
    raise; validation just surfaces it earlier.
    """
    tags = ['error']
    error_type = 'DefinitionError'
    action = 'validate'
    template = {'greeting': {'$': 'attr', 'nmae': 'name'}}
    error = (
        'unknown `nmae` for `attr` rule\n'
        '  at template → greeting → attr'
    )


class ErrorDataNotIterable(base.ErrorBaseCase):
    """
    **`TransformationError` — data that doesn't fit the template.**

    The template is valid, but the input doesn't match what a rule expects: `map`
    needs something iterable and gets the number `5`. That's a *data* problem, so it
    raises `TransformationError` (not `DefinitionError`). The location threads through
    the whole nesting — ``at template → result → chain → funcs[1] → map`` — so even in
    a deep template you land on the exact failing rule.
    """
    tags = ['error']
    error_type = 'TransformationError'
    template = {
        'result': {
            '$': 'chain',
            'funcs': [
                {'$': 'attr', 'name': 'items'},
                {'$': 'map', 'item': {'$': 'attr', 'name': 'sku'}},
            ],
        },
    }
    data = {'items': 5}
    error = (
        'value is not iterable: 5\n'
        '  at template → result → chain → funcs[1] → map'
    )


class ErrorIncompatibleOperands(base.ErrorBaseCase):
    """
    **`TransformationError` — incompatible operands in an expression.**

    Expressions fail at transform time when the operands don't fit the operator: here
    `+` is asked to add the string `"x"` and the number `1`. The template is
    well-formed, so this is a `TransformationError`, located at the expression node
    (``at template → expr``).
    """
    tags = ['error']
    error_type = 'TransformationError'
    template = {
        '$': 'expr',
        'op': '+',
        'values': [
            {'$': 'this'},
            1,
        ],
    }
    data = 'x'
    error = (
        "expr operator '+' failed on incompatible operands\n"
        '  at template → expr'
    )
