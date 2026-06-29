from transon import (
    Transformer,
    DefinitionError,
)
from transon.transformers import format_error_message


def _json_type(value):
    """Return the JSON type name of ``value``.

    Total over every JSON-shaped value and never raises on well-formed data, so it
    is safe to apply to an unknown node inside a non-throwing ``switch``/``cond`` key.
    """
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, int):
        return 'int'
    if isinstance(value, float):
        return 'float'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    raise DefinitionError(format_error_message(  # pragma: no cover - unreachable for JSON data
        f'`type` is undefined for non-JSON value of Python type {type(value).__name__!r}'
    ))


Transformer.register_function(
    'str', input_type='any', output_type='str',
    doc='Convert any value to its string representation (Python `str`).',
)(str)
Transformer.register_function(
    'int', input_type='str', output_type='int',
    doc='Parse a string (or number) into an integer (Python `int`). An optional base can '
        'be passed as a second value.',
)(int)
Transformer.register_function(
    'float', input_type='str', output_type='float',
    doc='Parse a string (or number) into a floating-point number (Python `float`).',
)(float)
Transformer.register_function(
    'type', input_type='any', output_type='string',
    doc='Return the JSON type of a value: one of `object`, `array`, `string`, `int`, '
        '`float`, `boolean`, or `null`. Total — never raises on well-formed JSON, so it '
        'is the one operation a `switch`/`cond` key can safely apply to an unknown node.',
)(_json_type)
