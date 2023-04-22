import operator
from functools import reduce

from transon import (
    Transformer,
    Context,
    TransformationError,
    DefinitionError,
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
def rule_parent(_t: Transformer, _template, context: Context):
    """
    Returns the value stored in previous context.
    """
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
    name="Name of the variable. Can be dynamic.",
)
def rule_set(t: Transformer, template, context: Context):
    """
    Stores the value in the context under given name.
    You can consider this rule as variable assignment.
    Variable will be accessible under that name in all underlying contexts.
    """
    t_name = t.require(template, 'name')
    name = t.walk(t_name, context)
    context[name] = context.this
    return context.this


@Transformer.register_rule(
    'get',
    name="Name of the variable. Can be dynamic.",
)
def rule_get(t: Transformer, template, context: Context):
    """
    Returns the value stored under given name.
    Value may be stored in current context or in any previous contexts.
    """
    t_name = t.require(template, 'name')
    name = t.walk(t_name, context)
    if name in context:
        return context[name]
    return t.NO_CONTENT


@Transformer.register_rule(
    'attr',
    name="""
Name of attribute to search. 
It is possible to use a number as the name for items in arrays. 
Can be dynamic.
""",
    names="""
List of attribute names or indexes to search in nested structure. 
Can be dynamic.
""",
)
def rule_attr(t: Transformer, template, context: Context):
    """
    Returns values of attribute or item from current value in context.
    Can search in deeply nested structures with path.
    If attribute is not present returns no value.

    Parameters are mutually exclusive.
    """
    if 'name' in template:
        t_name = template['name']
        name = t.walk(t_name, context)
        try:
            return context.this[name]
        except KeyError:
            return t.NO_CONTENT
        except IndexError:
            return t.NO_CONTENT
    elif 'names' in template:
        t_names = template['names']
        names = t.walk(t_names, context)
        try:
            return reduce(operator.getitem, names, context.this)
        except KeyError:
            return t.NO_CONTENT
        except IndexError:
            return t.NO_CONTENT
    else:
        raise DefinitionError('either `name` of `names` attribute is required for `attr` rule')


@Transformer.register_rule(
    'object',
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
    key = t.walk(t_key, context)
    value = t.walk(t_value, context)
    if key is t.NO_CONTENT:
        return {}
    if value is t.NO_CONTENT:
        return {}
    return {key: value}


def _iter_contexts(context: Context):
    data = context.this
    if isinstance(data, list):
        for index, _item in enumerate(data):
            yield context.derive(this=_item, index=index, item=_item)
    elif isinstance(data, dict):
        for index, (_key, _value) in enumerate(data.items()):
            yield context.derive(this=_value, index=index, key=_key, value=_value)
    else:
        raise TransformationError(f"value is not iterable: {data!r}")


@Transformer.register_rule(
    'map',
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
        for sub_context in _iter_contexts(context):
            item = t.walk(t_item, sub_context)
            if item is t.NO_CONTENT:
                continue
            result.append(item)
        return result
    elif 'items' in template:
        t_items = template['items']
        result = []
        for sub_context in _iter_contexts(context):
            for item in t.walk(t_items, sub_context):
                if item is t.NO_CONTENT:
                    continue
                result.append(item)
        return result
    elif 'key' in template and 'value' in template:
        t_key = template['key']
        t_value = template['value']
        result = {}
        for sub_context in _iter_contexts(context):
            key = t.walk(t_key, sub_context)
            value = t.walk(t_value, sub_context)
            if key is t.NO_CONTENT:
                continue
            if value is t.NO_CONTENT:
                continue
            result[key] = value
        return result

    raise DefinitionError(
        'either `item` or `items` or `key/value` properties '
        'are required for `map` rule'
    )


@Transformer.register_rule(
    'filter',
    cond="Defines template for condition",
)
def rule_filter(t: Transformer, template, context: Context):
    """
    Iterates over `list` or `dict` and filters out items regarding condition calculation.
    """

    t_cond = t.require(template, 'cond')

    def _iterate_with_condition(_context: Context):
        for _sub_context in _iter_contexts(_context):
            cond = t.walk(t_cond, _sub_context)
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
        raise TransformationError(f"value is not iterable: {data!r}")


@Transformer.register_rule(
    'zip',
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
    items = t.walk(t_items, context)
    return list(zip(*items))


@Transformer.register_rule(
    'file',
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
    name = t.walk(t_name, context)
    content = t.walk(t_content, context)
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
    items="List of values to concatenate.",
    sep="Defines separator for strings concatenation.",
)
def rule_join(t: Transformer, template, context: Context):
    """
    Joins (concatenates) together several dicts, lists of strings.
    If items to be concatenated have different types an exception will be thrown.
    """
    t_items = t.require(template, 'items')
    items = t.walk(t_items, context)
    if all(map(_is_str, items)):
        sep = template.get('sep', '')
        return sep.join(items)
    elif all(map(_is_list, items)):
        return sum(items, [])
    elif all(map(_is_dict, items)):
        result = {}
        for item in items:
            result.update(item)
        return result
    raise TransformationError("Can't join items")


@Transformer.register_rule(
    'chain',
    funcs="Define list of templates (not just rules) for chaining",
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
    for t_func in t_funcs:
        value = t.walk(t_func, local_context)
        local_context = local_context.derive(this=value)
    return local_context.this


@Transformer.register_rule(
    'expr',
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
    | &&           | and         | binary | boolean        | boolean        |
    | &#124;&#124; | or          | binary | boolean        | boolean        |
    | !            | not         | unary  | boolean        | boolean        |

    You can use code-style or mnemonic name (i.e. operator or alternative). 
""",
    value="Defines template for single parameter value",
    values="Defines template for multiple parameters values",
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

    if 'value' in template:
        t_value = template['value']
        value = t.walk(t_value, context)
        return op(context.this, value)
    elif 'values' in template:
        t_values = template['values']
        values = t.walk(t_values, context)
        return reduce(op, values)
    else:
        return op(context.this)


@Transformer.register_rule(
    'call',
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

    if 'value' in template:
        t_value = template['value']
        value = t.walk(t_value, context)
        return function(value)
    elif 'values' in template:
        t_values = template['values']
        values = t.walk(t_values, context)
        return function(*values)
    else:
        return function(context.this)


@Transformer.register_rule(
    'format',
    pattern="Defines pattern for string formatting. This is always a constant.",
    value="Defines template for input data. Optional.",
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
    """
    pattern = t.require(template, 'pattern')
    value = context.this
    if 'value' in template:
        t_value = template['value']
        value = t.walk(t_value, context)
    if isinstance(value, list):
        return pattern.format(*value)
    elif isinstance(value, dict):
        return pattern.format(**value)
    else:
        return pattern.format(value)


@Transformer.register_rule(
    'include',
    name="Name or path to template. Can be dynamic. Meaning of this `name` depends on provided template loader.",
)
def rule_include(t: Transformer, template, context: Context):
    t_name = t.require(template, 'name')
    name = t.walk(t_name, context)
    sub_transformer = t.template_loader(name)
    result = sub_transformer.transform(context.this)
    return t.NO_CONTENT if result is sub_transformer.NO_CONTENT else result
