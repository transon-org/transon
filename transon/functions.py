import base64
import binascii
import math
import re
import uuid
from datetime import datetime, timezone

from transon import (
    Transformer,
    DefinitionError,
    TransformationError,
)
from transon.transformers import format_error_message


_ISO_EPOCH_FMT = '%Y-%m-%dT%H:%M:%SZ'
_EPOCH_FMT_ALLOWED = frozenset('YmdHMSjz%')
_UUID5_NAMESPACES = {
    'dns': uuid.NAMESPACE_DNS,
    'url': uuid.NAMESPACE_URL,
    'oid': uuid.NAMESPACE_OID,
    'x500': uuid.NAMESPACE_X500,
}


def _error(message):
    raise TransformationError(format_error_message(message))


def _require_str(value, name):
    if not isinstance(value, str):
        _error(f'`{name}` requires a string, got {type(value).__name__}')
    return value


def _require_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _error(f'`{name}` requires a number, got {type(value).__name__}')
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        _error(f'`{name}` rejects non-finite number {value!r}')
    return value


def _is_scalar(value):
    return value is None or isinstance(value, (bool, int, float, str))


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


def _upper(value):
    return _require_str(value, 'upper').upper()


def _lower(value):
    return _require_str(value, 'lower').lower()


def _capitalize(value):
    return _require_str(value, 'capitalize').capitalize()


def _replace(s, old, new):
    return _require_str(s, 'replace').replace(
        _require_str(old, 'replace'),
        _require_str(new, 'replace'),
    )


def _removeprefix(s, prefix):
    return _require_str(s, 'removeprefix').removeprefix(
        _require_str(prefix, 'removeprefix')
    )


def _removesuffix(s, suffix):
    return _require_str(s, 'removesuffix').removesuffix(
        _require_str(suffix, 'removesuffix')
    )


def _strip(s, chars=None):
    s = _require_str(s, 'strip')
    if chars is None:
        return s.strip()
    return s.strip(_require_str(chars, 'strip'))


def _lstrip(s, chars=None):
    s = _require_str(s, 'lstrip')
    if chars is None:
        return s.lstrip()
    return s.lstrip(_require_str(chars, 'lstrip'))


def _rstrip(s, chars=None):
    s = _require_str(s, 'rstrip')
    if chars is None:
        return s.rstrip()
    return s.rstrip(_require_str(chars, 'rstrip'))


def _slice(x, start, stop=None):
    if not isinstance(x, (str, list)):
        _error(f'`slice` requires a string or array, got {type(x).__name__}')
    if isinstance(start, bool) or not isinstance(start, int):
        _error(f'`slice` start must be an int, got {type(start).__name__}')
    if stop is None:
        return x[start:]
    if isinstance(stop, bool) or not isinstance(stop, int):
        _error(f'`slice` stop must be an int, got {type(stop).__name__}')
    return x[start:stop]


def _validate_epoch_fmt(fmt):
    if not isinstance(fmt, str):
        _error(f'epoch format must be a string, got {type(fmt).__name__}')
    i = 0
    while i < len(fmt):
        if fmt[i] != '%':
            i += 1
            continue
        if i + 1 >= len(fmt):
            _error(f'epoch format has a trailing `%`: {fmt!r}')
        directive = fmt[i + 1]
        if directive not in _EPOCH_FMT_ALLOWED:
            _error(
                f'epoch format rejects locale-sensitive or unsupported directive '
                f'`%{directive}` in {fmt!r}'
            )
        i += 2


def _from_epoch(n, fmt=None):
    n = _require_number(n, 'from_epoch')
    try:
        dt = datetime.fromtimestamp(int(n), tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        _error(f'`from_epoch` epoch seconds out of range: {n!r}')
    if fmt is None:
        return dt.strftime(_ISO_EPOCH_FMT)
    _validate_epoch_fmt(fmt)
    try:
        return dt.strftime(fmt)
    except (ValueError, OverflowError) as exc:  # pragma: no cover - whitelist formats succeed
        _error(f'`from_epoch` failed to format: {exc}')


def _to_epoch(s, fmt=None):
    s = _require_str(s, 'to_epoch')
    if fmt is None:
        fmt = _ISO_EPOCH_FMT
    else:
        _validate_epoch_fmt(fmt)
    try:
        dt = datetime.strptime(s, fmt)
    except ValueError as exc:
        _error(f'`to_epoch` failed to parse {s!r} with format {fmt!r}: {exc}')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return int(dt.timestamp())


def _length(value):
    if isinstance(value, (str, list, dict)):
        return len(value)
    _error(f'`length` requires a string, array, or object, got {type(value).__name__}')


def _flatten(value):
    if not isinstance(value, list):
        _error(f'`flatten` requires an array, got {type(value).__name__}')
    result = []
    for item in value:
        if not isinstance(item, list):
            _error('`flatten` requires every element to be an array')
        result.extend(item)
    return result


def _sum(value):
    if not isinstance(value, list):
        _error(f'`sum` requires an array, got {type(value).__name__}')
    total = 0
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            _error(f'`sum` requires numeric elements, got {type(item).__name__}')
        total += item
    return total


def _min_max(name, array, default=None, *, has_default=False):
    if not isinstance(array, list):
        _error(f'`{name}` requires an array, got {type(array).__name__}')
    if not array:
        if has_default:
            return default
        _error(f'`{name}` of an empty array requires a default')
    try:
        return (min if name == 'min' else max)(array)
    except TypeError:
        _error(f'`{name}` requires comparable homogeneous elements')


def _min_call(*args):
    if len(args) == 1:
        return _min_max('min', args[0], has_default=False)
    if len(args) == 2:
        return _min_max('min', args[0], args[1], has_default=True)
    _error(f'`min` expects 1 or 2 arguments, got {len(args)}')


def _max_call(*args):
    if len(args) == 1:
        return _min_max('max', args[0], has_default=False)
    if len(args) == 2:
        return _min_max('max', args[0], args[1], has_default=True)
    _error(f'`max` expects 1 or 2 arguments, got {len(args)}')


def _sorted(value):
    if not isinstance(value, list):
        _error(f'`sorted` requires an array, got {type(value).__name__}')
    if not value:
        return []
    if not all(_is_scalar(item) for item in value):
        _error('`sorted` requires scalar elements')

    def _kind(item):
        if item is None:
            return 'null'
        if isinstance(item, bool):
            return 'boolean'
        if isinstance(item, str):
            return 'string'
        if isinstance(item, (int, float)):
            return 'number'
        return type(item).__name__  # pragma: no cover - guarded by _is_scalar

    kinds = {_kind(item) for item in value}
    if len(kinds) > 1:
        _error('`sorted` requires homogeneous scalar types')
    try:
        return sorted(value)
    except TypeError:
        _error('`sorted` requires comparable homogeneous elements')


def _reversed(value):
    if isinstance(value, list):
        return list(reversed(value))
    if isinstance(value, str):
        return value[::-1]
    _error(f'`reversed` requires a string or array, got {type(value).__name__}')


def _unique(value):
    if not isinstance(value, list):
        _error(f'`unique` requires an array, got {type(value).__name__}')
    seen = set()
    result = []
    for item in value:
        if isinstance(item, (dict, list)):
            _error('`unique` rejects object or array elements')
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _abs(value):
    return abs(_require_number(value, 'abs'))


def _floor(value):
    return math.floor(_require_number(value, 'floor'))


def _ceil(value):
    return math.ceil(_require_number(value, 'ceil'))


def _round(value, ndigits=None):
    value = _require_number(value, 'round')
    if ndigits is None:
        return round(value)
    if isinstance(ndigits, bool) or not isinstance(ndigits, int):
        _error(f'`round` ndigits must be an int, got {type(ndigits).__name__}')
    return round(value, ndigits)


def _bool(value):
    return bool(value)


def _b64encode(value):
    try:
        raw = _require_str(value, 'b64encode').encode('utf-8')
    except UnicodeEncodeError as exc:
        _error(f'`b64encode` string is not UTF-8 encodable: {exc}')
    return base64.b64encode(raw).decode('ascii')


def _b64decode(value):
    s = _require_str(value, 'b64decode')
    try:
        raw = base64.b64decode(s, validate=True)
    except (binascii.Error, ValueError) as exc:
        _error(f'`b64decode` invalid base64: {exc}')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        _error(f'`b64decode` payload is not UTF-8: {exc}')


def _uuid5(namespace, name):
    name = _require_str(name, 'uuid5')
    if isinstance(namespace, str) and namespace in _UUID5_NAMESPACES:
        ns = _UUID5_NAMESPACES[namespace]
    else:
        try:
            ns = uuid.UUID(_require_str(namespace, 'uuid5'))
        except (ValueError, AttributeError, TypeError):
            _error(
                '`uuid5` namespace must be one of dns/url/oid/x500 or a UUID string'
            )
    return str(uuid.uuid5(ns, name))


def _regex_match(s, pattern):
    s = _require_str(s, 'regex_match')
    pattern = _require_str(pattern, 'regex_match')
    try:
        match = re.search(pattern, s)
    except re.error as exc:
        _error(f'`regex_match` invalid pattern: {exc}')
    if match is None:
        return None
    if match.re.groups:
        return list(match.groups())
    return [match.group(0)]


def _regex_replace(s, pattern, repl):
    s = _require_str(s, 'regex_replace')
    pattern = _require_str(pattern, 'regex_replace')
    repl = _require_str(repl, 'regex_replace')
    try:
        return re.sub(pattern, repl, s)
    except re.error as exc:
        _error(f'`regex_replace` invalid pattern: {exc}')


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
Transformer.register_function(
    'bool', input_type='any', output_type='boolean',
    doc='Convert any value to a boolean by Python truthiness. Total — never raises. '
        'Useful to turn `regex_match` (groups-or-null) into a condition predicate.',
)(_bool)

Transformer.register_function(
    'upper', input_type='string', output_type='string',
    doc='Return `s` uppercased. Non-string input raises `TransformationError`.',
)(_upper)
Transformer.register_function(
    'lower', input_type='string', output_type='string',
    doc='Return `s` lowercased. Non-string input raises `TransformationError`.',
)(_lower)
Transformer.register_function(
    'capitalize', input_type='string', output_type='string',
    doc='Return `s` with the first character uppercased and the rest lowercased. '
        'Non-string input raises `TransformationError`.',
)(_capitalize)
Transformer.register_function(
    'replace', input_type='string', output_type='string',
    doc='`values: [s, old, new]` — replace all occurrences of `old` with `new` in `s`.',
)(_replace)
Transformer.register_function(
    'removeprefix', input_type='string', output_type='string',
    doc='`values: [s, prefix]` — remove `prefix` from the start of `s` if present. '
        'Unlike `lstrip`, this is exact-prefix removal, not character-set trimming.',
)(_removeprefix)
Transformer.register_function(
    'removesuffix', input_type='string', output_type='string',
    doc='`values: [s, suffix]` — remove `suffix` from the end of `s` if present. '
        'Unlike `rstrip`, this is exact-suffix removal, not character-set trimming.',
)(_removesuffix)
Transformer.register_function(
    'strip', input_type='string', output_type='string',
    doc='Strip leading/trailing whitespace, or `values: [s, chars]` for a character set. '
        'Not a substitute for `removeprefix`/`removesuffix`.',
)(_strip)
Transformer.register_function(
    'lstrip', input_type='string', output_type='string',
    doc='Strip leading whitespace, or `values: [s, chars]` for a character set.',
)(_lstrip)
Transformer.register_function(
    'rstrip', input_type='string', output_type='string',
    doc='Strip trailing whitespace, or `values: [s, chars]` for a character set.',
)(_rstrip)

Transformer.register_function(
    'slice', input_type='string, array', output_type='string, array',
    doc='`values: [x, start]` or `[x, start, stop]` — Python slice of a string or array. '
        'Negative indices and out-of-range clamps apply. Non-int indices raise '
        '`TransformationError`.',
)(_slice)

Transformer.register_function(
    'from_epoch', input_type='number', output_type='string',
    doc='Convert epoch **seconds** (int/float; fractional truncated) to a UTC string. '
        'Unary form uses fixed ISO-8601 `YYYY-MM-DDThh:mm:ssZ`. '
        '`values: [n, fmt]` uses an explicit format restricted to '
        '`%Y %m %d %H %M %S %j %z %%` plus literal text. Non-finite or out-of-range '
        'inputs and disallowed directives raise `TransformationError`.',
)(_from_epoch)
Transformer.register_function(
    'to_epoch', input_type='string', output_type='int',
    doc='Parse a UTC date/time string to epoch seconds (int). '
        '`values: [s]` accepts fixed ISO-8601 `YYYY-MM-DDThh:mm:ssZ`; '
        '`values: [s, fmt]` uses an explicit format with the same whitelist as '
        '`from_epoch`. Parse failure raises `TransformationError`.',
)(_to_epoch)

Transformer.register_function(
    'length', input_type='string, array, object', output_type='int',
    doc='Return the length of a string, array, or object. Other types raise '
        '`TransformationError`.',
)(_length)
Transformer.register_function(
    'flatten', input_type='array', output_type='array',
    doc='Flatten one level of an array-of-arrays. Non-array input or a non-array '
        'element raises `TransformationError`.',
)(_flatten)
Transformer.register_function(
    'sum', input_type='array', output_type='number',
    doc='Sum an array of numbers. `sum([])` is `0`. Booleans and non-numeric elements '
        'raise `TransformationError`.',
)(_sum)
Transformer.register_function(
    'min', input_type='array', output_type='any',
    doc='`values: [array]` or `[array, default]` — minimum element. Empty array without '
        '`default` raises `TransformationError`.',
)(_min_call)
Transformer.register_function(
    'max', input_type='array', output_type='any',
    doc='`values: [array]` or `[array, default]` — maximum element. Empty array without '
        '`default` raises `TransformationError`.',
)(_max_call)
Transformer.register_function(
    'sorted', input_type='array', output_type='array',
    doc='Return a new array of homogeneous scalars sorted ascending. Mixed types raise '
        '`TransformationError`.',
)(_sorted)
Transformer.register_function(
    'reversed', input_type='string, array', output_type='string, array',
    doc='Reverse an array or a string. Other types raise `TransformationError`.',
)(_reversed)
Transformer.register_function(
    'unique', input_type='array', output_type='array',
    doc='Deduplicate an array preserving first-occurrence order. Object or array '
        'elements raise `TransformationError`.',
)(_unique)
Transformer.register_function(
    'abs', input_type='number', output_type='number',
    doc='Absolute value of a number. Non-number raises `TransformationError`.',
)(_abs)
Transformer.register_function(
    'floor', input_type='number', output_type='int',
    doc='Floor of a number (`math.floor`). Non-number raises `TransformationError`.',
)(_floor)
Transformer.register_function(
    'ceil', input_type='number', output_type='int',
    doc='Ceiling of a number (`math.ceil`). Non-number raises `TransformationError`.',
)(_ceil)
Transformer.register_function(
    'round', input_type='number', output_type='number',
    doc='Round a number; optional `values: [x, ndigits]`. Non-number raises '
        '`TransformationError`.',
)(_round)

Transformer.register_function(
    'b64encode', input_type='string', output_type='string',
    doc='UTF-8 encode a string and return standard-alphabet base64.',
)(_b64encode)
Transformer.register_function(
    'b64decode', input_type='string', output_type='string',
    doc='Decode standard-alphabet base64 to a UTF-8 string. Invalid base64 or '
        'non-UTF-8 payload raises `TransformationError`.',
)(_b64decode)
Transformer.register_function(
    'uuid5', input_type='string', output_type='string',
    doc='`values: [namespace, name]` — deterministic UUID5. `namespace` is one of '
        '`dns`/`url`/`oid`/`x500` or a UUID string. Pure and reproducible '
        '(no random `uuid4`).',
)(_uuid5)
Transformer.register_function(
    'regex_match', input_type='string', output_type='array, null',
    doc='`values: [s, pattern]` — Python `re.search`. On match returns capture groups '
        'as an array (unmatched optionals are `null`); with no groups returns '
        '`[full match]`. On no match returns `null`. Use `bool(...)` in conditions. '
        'Invalid pattern raises `TransformationError`. Dialect is Python `re`; ReDoS '
        'is a host responsibility.',
)(_regex_match)
Transformer.register_function(
    'regex_replace', input_type='string', output_type='string',
    doc='`values: [s, pattern, repl]` — Python `re.sub`. Invalid pattern raises '
        '`TransformationError`. Dialect is Python `re`; ReDoS is a host responsibility.',
)(_regex_replace)
