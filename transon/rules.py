import operator
from functools import reduce

from transon import (
    Transformer,
    Context,
    TransformationError,
    DefinitionError,
)

_transon_errors = (DefinitionError, TransformationError)


def _require_variable_name(t: Transformer, name):
    if name is Transformer.NO_CONTENT:
        t.transformation_error(
            'variable name cannot be no value (name evaluated to NO_CONTENT)'
        )


def _apply_default(t, template, context, value):
    if value is t.NO_CONTENT and 'default' in template:
        return t.walk_param(template['default'], context, 'default')
    return value


def _format_value_contains_no_content(value, no_content):
    if value is no_content:
        return True
    if isinstance(value, list):
        for item in value:
            if item is no_content:
                return True
    elif isinstance(value, dict):
        for key, item in value.items():
            if key is no_content or item is no_content:
                return True
    return False


def _attr_lookup(t: Transformer, container, names):
    no_content = Transformer.NO_CONTENT
    if names is no_content:
        return no_content
    if isinstance(names, list):
        for segment in names:
            if segment is no_content:
                return no_content
    try:
        if isinstance(names, list):
            return reduce(operator.getitem, names, container)
        return container[names]
    except KeyError:
        return Transformer.NO_CONTENT
    except IndexError:
        return Transformer.NO_CONTENT
    except TypeError as exc:
        t.transformation_error(
            'cannot access attribute or index on value of type '
            f'{type(container).__name__}'
        )


@Transformer.register_rule('this')
def rule_this(_t: Transformer, _template, context: Context):
    """
    Returns the value stored in current transformation context.
    The root context has the value equals to input of transformation.
    Each operation creates new context with value of its result.
    """
    return context.this


@Transformer.register_rule('parent')
def rule_parent(t: Transformer, _template, context: Context):
    """
    Returns the value stored in previous context.
    """
    if context.parent is None:
        t.definition_error('`parent` is not available in the root context')
    return context.parent.this


@Transformer.register_rule('item')
def rule_item(_t: Transformer, _template, context: Context):
    """
    Works inside `map` rule when iterating over lists.
    Returns current item.
    """
    return context.item


@Transformer.register_rule('key')
def rule_key(_t: Transformer, _template, context: Context):
    """
    Works inside `map` rule when iterating over dicts.
    Returns the key of current element.
    """
    return context.key


@Transformer.register_rule('index')
def rule_index(_t: Transformer, _template, context: Context):
    """
    Works inside `map` rule.
    Returns 0-based index of iteration.
    """
    return context.index


@Transformer.register_rule('value')
def rule_value(_t: Transformer, _template, context: Context):
    """
    Works inside `map` rule when iterating over dicts.
    Returns the value of current element.
    """
    return context.value


@Transformer.register_rule(
    'set',
    _required=('name',),
    name="Name of the variable. Can be dynamic. "
         "The names `this`, `item`, `key`, `value` and `index` are reserved "
         "and cannot be used as variable names. "
         "Raises `TransformationError` if the name evaluates to `NO_CONTENT`.",
)
def rule_set(t: Transformer, template, context: Context):
    """
    Stores the value in the context under given name.
    You can consider this rule as variable assignment.
    Variable will be accessible under that name in all underlying contexts.
    """
    t_name = t.require(template, 'name')
    name = t.walk_param(t_name, context, 'name')
    _require_variable_name(t, name)
    context[name] = context.this
    return context.this


@Transformer.register_rule(
    'get',
    _required=('name',),
    name="Name of the variable. Can be dynamic. "
         "The names `this`, `item`, `key`, `value` and `index` are reserved "
         "and cannot be used as variable names. "
         "Raises `TransformationError` if the name evaluates to `NO_CONTENT`.",
    default="Optional template for value returned when the variable is undefined. "
            "Can be dynamic.",
)
def rule_get(t: Transformer, template, context: Context):
    """
    Returns the value stored under given name.
    Value may be stored in current context or in any previous contexts.
    """
    t_name = t.require(template, 'name')
    name = t.walk_param(t_name, context, 'name')
    _require_variable_name(t, name)
    if name in context:
        return context[name]
    return _apply_default(t, template, context, t.NO_CONTENT)


@Transformer.register_rule(
    'attr',
    _modes=(('name',), ('names',)),
    name="""
Name of attribute to search. 
It is possible to use a number as the name for items in arrays. 
Can be dynamic.
""",
    names="""
List of attribute names or indexes to search in nested structure. 
Can be dynamic.
""",
    default="Optional template for value returned when the attribute or path is "
            "missing. Can be dynamic.",
)
def rule_attr(t: Transformer, template, context: Context):
    """
    Returns values of attribute or item from current value in context.
    Can search in deeply nested structures with path.
    If attribute is not present returns no value.
    If the dynamic name or any path segment evaluates to `NO_CONTENT`, returns
    no value (uniformly for all container types).

    Parameters are mutually exclusive.
    """
    if 'name' in template:
        t_name = template['name']
        name = t.walk_param(t_name, context, 'name')
        result = _attr_lookup(t, context.this, name)
    elif 'names' in template:
        t_names = template['names']
        names = t.walk_param(t_names, context, 'names')
        result = _attr_lookup(t, context.this, names)
    else:
        t.definition_error(
            'either `name` of `names` attribute is required for `attr` rule'
        )
    return _apply_default(t, template, context, result)


@Transformer.register_rule(
    'object',
    _required=('key', 'value'),
    key="Defines template for name of attribute.",
    value="Defines template for value of attribute.",
)
def rule_object(t: Transformer, template, context: Context):
    """
    Returns a dict with one item.
    This is useful when you need dynamically named attributes.
    If you need multiple attributes use `join` or `map`.
    If `key` or `value` returns no result then the rule returns empty dict.
    """
    t_key = t.require(template, 'key')
    t_value = t.require(template, 'value')
    key = t.walk_param(t_key, context, 'key')
    value = t.walk_param(t_value, context, 'value')
    if key is t.NO_CONTENT:
        return {}
    if value is t.NO_CONTENT:
        return {}
    return {key: value}


def _iter_contexts(t: Transformer, context: Context):
    data = context.this
    if isinstance(data, list):
        for index, _item in enumerate(data):
            yield context.derive(this=_item, index=index, item=_item)
    elif isinstance(data, dict):
        for index, (_key, _value) in enumerate(data.items()):
            yield context.derive(this=_value, index=index, key=_key, value=_value)
    else:
        t.transformation_error(f"value is not iterable: {data!r}")


@Transformer.register_rule(
    'map',
    _modes=(('item',), ('items',), ('key', 'value')),
    item="Defines template for items when producing the `list`",
    items="Defines templates for series of items when producing the `list`",
    key="Defines template for key when producing the `dict`",
    value="Defines template for value when producing the `dict`",
)
def rule_map(t: Transformer, template, context: Context):
    """
    Iterates over `list` or `dict` and produces new `dict` or `list` with items based on template.
    """
    if 'item' in template:
        t_item = template['item']
        result = []
        for sub_context in _iter_contexts(t, context):
            item = t.walk_param(t_item, sub_context, 'item')
            if item is t.NO_CONTENT:
                continue
            result.append(item)
        return result
    elif 'items' in template:
        t_items = template['items']
        result = []
        for sub_context in _iter_contexts(t, context):
            for item in t.walk_param(t_items, sub_context, 'items'):
                if item is t.NO_CONTENT:
                    continue
                result.append(item)
        return result
    elif 'key' in template and 'value' in template:
        t_key = template['key']
        t_value = template['value']
        result = {}
        for sub_context in _iter_contexts(t, context):
            key = t.walk_param(t_key, sub_context, 'key')
            value = t.walk_param(t_value, sub_context, 'value')
            if key is t.NO_CONTENT:
                continue
            if value is t.NO_CONTENT:
                continue
            result[key] = value
        return result

    t.definition_error(
        'either `item` or `items` or `key/value` properties '
        'are required for `map` rule'
    )


@Transformer.register_rule(
    'filter',
    _required=('cond',),
    cond="Defines template for condition",
)
def rule_filter(t: Transformer, template, context: Context):
    """
    Iterates over `list` or `dict` and filters out items regarding condition calculation.
    """

    t_cond = t.require(template, 'cond')

    def _iterate_with_condition(_context: Context):
        for _sub_context in _iter_contexts(t, _context):
            cond = t.walk_param(t_cond, _sub_context, 'cond')
            if cond is t.NO_CONTENT:
                continue
            if not cond:
                continue
            yield _sub_context

    data = context.this
    if isinstance(data, list):
        return [
            sub_context.item
            for sub_context in _iterate_with_condition(context)
        ]
    elif isinstance(data, dict):
        return {
            sub_context.key: sub_context.value
            for sub_context in _iterate_with_condition(context)
        }
    else:
        t.transformation_error(f"value is not iterable: {data!r}")


@Transformer.register_rule(
    'zip',
    _required=('items',),
    items="Defines the list of lists",
)
def rule_zip(t: Transformer, template, context: Context):
    """
    Works exactly like `zip` function in python.
    Converts collection of lists into list of items.
    Another way to think of `zip` is that it turns rows into columns, and columns into rows.
    This is similar to transposing a matrix.
    """

    t_items = t.require(template, 'items')
    items = t.walk_param(t_items, context, 'items')
    try:
        return list(zip(*items))
    except TypeError as exc:
        t.transformation_error(
            f'zip items must be iterable lists: {exc}'
        )


@Transformer.register_rule(
    'file',
    _required=('name', 'content'),
    name="Defines template for file name",
    content="Defines template for file content. File content always has JSON formatted data",
)
def rule_file(t: Transformer, template, context: Context):
    """
    Writes a file using `write_file` delegate (a parameter to `Transformer` constructor).
    This rule produces no result.
    File will not be written if `name` or `content` returns no result.
    """
    def write_file(_name, _content):
        if _name is t.NO_CONTENT:
            return
        if _content is t.NO_CONTENT:
            return
        t.write_file(_name, _content)

    t_name = t.require(template, 'name')
    t_content = t.require(template, 'content')
    name = t.walk_param(t_name, context, 'name')
    content = t.walk_param(t_content, context, 'content')
    write_file(name, content)
    return t.NO_CONTENT


def _is_str(x):
    return isinstance(x, str)


def _is_list(x):
    return isinstance(x, list)


def _is_dict(x):
    return isinstance(x, dict)


@Transformer.register_rule(
    'join',
    _required=('items',),
    items="List of values to concatenate.",
    sep="Defines separator for strings concatenation. Can be dynamic. "
        "Used only when all items are strings; must evaluate to a string "
        "(raises `TransformationError` otherwise). Defaults to empty string.",
)
def rule_join(t: Transformer, template, context: Context):
    """
    Joins (concatenates) together several dicts, lists of strings.
    If items to be concatenated have different types an exception will be thrown.
    Items that evaluate to `NO_CONTENT` are omitted before concatenation.
    """
    t_items = t.require(template, 'items')
    items = t.walk_param(t_items, context, 'items')
    items = [item for item in items if item is not t.NO_CONTENT]
    if all(map(_is_str, items)):
        sep = ''
        if 'sep' in template:
            sep = t.walk_param(template['sep'], context, 'sep')
            if sep is t.NO_CONTENT or not isinstance(sep, str):
                t.transformation_error(
                    '`sep` must evaluate to a string for string join'
                )
        return sep.join(items)
    elif all(map(_is_list, items)):
        return sum(items, [])
    elif all(map(_is_dict, items)):
        result = {}
        for item in items:
            result.update(item)
        return result
    t.transformation_error("Can't join items")


@Transformer.register_rule(
    'chain',
    _required=('funcs',),
    funcs="Define list of templates (not just rules) for chaining. "
          "The list structure is constant; each element is walked as a template.",
)
def rule_chain(t: Transformer, template, context: Context):
    """
    Function composition operation.
    Build function composition and executes it against value in current context.
    `chain(f1, f2, f3)(x) === f3(f2(f1(x)))`

    Each function execution creates new context that will be passed to next function.
    ```plantuml
    @startuml
    left to right direction
    rectangle this
    rectangle "intermediate context" as i1
    rectangle "intermediate context" as i2
    rectangle result
    this --> i1: f1
    i1 --> i2: f2
    i2 --> result: f3
    @enduml
    ```
    """
    t_funcs = t.require(template, 'funcs')
    local_context = context
    for index, t_func in enumerate(t_funcs):
        value = t.walk(t_func, local_context, t.path + (f'funcs[{index}]',))
        local_context = local_context.derive(this=value)
    return local_context.this


@Transformer.register_rule(
    'expr',
    _required=('op',),
    _modes=((), ('value',), ('values',)),
    op="""
    Defines name of operation. This is always constant.

    ###### Possible values:

    | operator     | alternative | kind   | types          | result         |
    |--------------|-------------|--------|----------------|----------------|
    | <            | lt          | binary | any            | boolean        |
    | <=           | le          | binary | any            | boolean        |
    | ==           | eq          | binary | any            | boolean        |
    | !=           | ne          | binary | any            | boolean        |
    | >=           | ge          | binary | any            | boolean        |
    | &gt;         | gt          | binary | any            | boolean        |
    | +            | add         | binary | string, number | string, number |
    | -            | sub         | binary | number         | number         |
    | *            | mul         | binary | number         | number         |
    | /            | div         | binary | number         | number         |
    | %            | mod         | binary | number         | number         |
    | &&           | and         | binary | any            | any            |
    | &#124;&#124; | or          | binary | any            | any            |
    | !            | not         | unary  | boolean        | boolean        |

    You can use code-style or mnemonic name (i.e. operator or alternative). 
""",
    value="Defines template for single parameter value",
    values="""
Defines template for multiple parameter values.

> **Warning:** Unlike unary mode and `value` mode, **`this` is not used** when `values`
> is specified. The operator is applied via `reduce(op, values)` over the evaluated
> list only. Include `{"$": "this"}` as a list item if you need the current context
> value in the reduction.
""",
)
def rule_expr(t: Transformer, template, context: Context):
    """
    Executes unary or binary operation.
    There are 3 modes of running this rule:

    1. **No attributes were specified:**
    Result is unary operation calculation against current context value.
    2. **Single `value` was specified:**
    Result is binary operation calculation where the
    first argument is current values of context and
    the second is specified value.
    3. **Multiple `values` were specified:**
    Result is calculated by applying operation to all values in pairs (reduction).
    In this case current context value is ignored.

    Parameters are mutually exclusive.
    """
    op_code = t.require(template, 'op')
    op = t.get_operator(op_code)

    def _apply_expr(fn):
        try:
            return fn()
        except _transon_errors:
            raise
        except TypeError as exc:
            t.transformation_error(
                f'expr operator {op_code!r} failed on incompatible operands'
            )

    if 'value' in template:
        t_value = template['value']
        value = t.walk_param(t_value, context, 'value')
        return _apply_expr(lambda: op(context.this, value))
    elif 'values' in template:
        t_values = template['values']
        values = t.walk_param(t_values, context, 'values')
        if not isinstance(values, list):
            t.definition_error('`values` must be a list for `expr` rule')
        if not values:
            t.definition_error(
                '`values` must contain at least one element for `expr` rule'
            )
        return _apply_expr(lambda: reduce(op, values))
    else:
        return _apply_expr(lambda: op(context.this))


@Transformer.register_rule(
    'call',
    _required=('name',),
    _modes=((), ('value',), ('values',)),
    name="""
    Defines the name of function. This is always constant.
    
    ###### Possible values:

    | name  | input | output |
    |-------|:-----:|:------:|
    | str   |  any  |  str   | 
    | int   |  str  |  int   | 
    | float |  str  | float  | 

""",
    value="Defines template for single parameter value",
    values="Defines template for multiple parameters values",
)
def rule_call(t: Transformer, template, context: Context):
    """
    Runs function registered in `Transformer`.
    Usually, that is used to convert values into different type, but you can also use it to call any function.

    There are 3 modes of running this rule:

    1. **No attributes were specified:**
    Runs conversion function with single parameter - value of current context.
    2. **Single `value` was specified:**
    Runs conversion function with single parameter - provided value.
    Current context is ignored in this case.
    3. **Multiple `values` were specified:**
    Runs conversion function with multiple parameters.
    Current context is ignored in this case.

    Parameters are mutually exclusive.
    """
    name = t.require(template, 'name')
    function = t.get_function(name)

    def _apply_call(fn):
        try:
            return fn()
        except _transon_errors:
            raise
        except TypeError as exc:
            t.transformation_error(
                f'call to {name!r} failed on incompatible arguments'
            )

    if 'value' in template:
        t_value = template['value']
        value = t.walk_param(t_value, context, 'value')
        return _apply_call(lambda: function(value))
    elif 'values' in template:
        t_values = template['values']
        values = t.walk_param(t_values, context, 'values')
        if not isinstance(values, list):
            t.definition_error('`values` must be a list for `call` rule')
        return _apply_call(lambda: function(*values))
    else:
        return _apply_call(lambda: function(context.this))


@Transformer.register_rule(
    'format',
    _required=('pattern',),
    pattern="Defines pattern for string formatting. Can be dynamic. "
            "Must evaluate to a string (raises `TransformationError` otherwise).",
    value="Defines template for input data. Optional.",
    default="Optional template for value returned when the formatting value (or any "
            "unpacked list element or dict key/value) is `NO_CONTENT`. Can be dynamic.",
)
def rule_format(t: Transformer, template, context: Context):
    """
    Execute string formatting using current value.

    If `value` is specified it is used for formatting otherwise current context value is used.

    See [this page](https://docs.python.org/3/tutorial/inputoutput.html#the-string-format-method)
    for examples of how formatting in python works.

    If value for formatting is `dict` it will be unpacked to separate names.
    If value is list if will be unpacked to separate items.
    Otherwise while value will be passed to formatting.

    Returns no value when the formatting value (or any unpacked list element or dict
    key/value) is `NO_CONTENT`, unless `default` is provided.
    """
    t_pattern = t.require(template, 'pattern')
    pattern = t.walk_param(t_pattern, context, 'pattern')
    if pattern is t.NO_CONTENT or not isinstance(pattern, str):
        t.transformation_error(
            '`pattern` must evaluate to a string for format'
        )
    value = context.this
    if 'value' in template:
        t_value = template['value']
        value = t.walk_param(t_value, context, 'value')
    if _format_value_contains_no_content(value, t.NO_CONTENT):
        return _apply_default(t, template, context, t.NO_CONTENT)
    try:
        if isinstance(value, list):
            return pattern.format(*value)
        elif isinstance(value, dict):
            return pattern.format(**value)
        else:
            return pattern.format(value)
    except (KeyError, IndexError) as exc:
        t.transformation_error(
            f'format pattern {pattern!r} references a missing key or index'
        )


@Transformer.register_rule(
    'include',
    _required=('name',),
    name="Name or path to template. Can be dynamic. Meaning of this `name` depends on provided template loader.",
    default="Optional template for value returned when the included template produces "
            "no result. Can be dynamic.",
)
def rule_include(t: Transformer, template, context: Context):
    """
    Loads and runs another template using the `template_loader` delegate
    (a parameter to `Transformer` constructor).

    Only the current context value is passed to the included template — variables
    stored with `set`/`get` and iteration accessors do not cross the boundary.

    Nested includes are limited by `max_include_depth` on `Transformer` (default 50).
    Exceeding the limit raises `TransformationError` with the include name chain.

    If the included template produces no result, this rule produces no result unless
    `default` is provided.
    """
    t_name = t.require(template, 'name')
    name = t.walk_param(t_name, context, 'name')
    stack = t._prepare_include(name)
    sub_transformer = t.template_loader(name)
    sub_transformer._include_stack = stack
    sub_transformer.max_include_depth = t.max_include_depth
    result = sub_transformer.transform(
        context.this,
        no_content=sub_transformer.NO_CONTENT,
    )
    if result is sub_transformer.NO_CONTENT:
        return _apply_default(t, template, context, t.NO_CONTENT)
    return result
