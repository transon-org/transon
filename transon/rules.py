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
    Works inside `map` operation when iterating over lists.
    Returns current item.
    """
    return context.item


@Transformer.register_rule('key')
def rule_key(_t: Transformer, _template, context: Context):
    """
    Works inside `map` operation when iterating over dicts.
    Returns the key of current element.
    """
    return context.key


@Transformer.register_rule('index')
def rule_index(_t: Transformer, _template, context: Context):
    """
    Works inside `map` operation.
    Returns 0-based index of iteration.
    """
    return context.index


@Transformer.register_rule('value')
def rule_value(_t: Transformer, _template, context: Context):
    """
    Works inside `map` operation when iterating over dicts.
    Returns the value of current element.
    """
    return context.value


@Transformer.register_rule(
    'set',
    name="Name of the variable. Can be dynamic.",
)
def rule_set(t: Transformer, template, context: Context):
    """
    Stores in the context value under given name.
    You can presume that as variable assignment.
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
    name="TODO: Describe",  # TODO: Describe
    names="TODO: Describe",  # TODO: Describe
)
def rule_attr(t: Transformer, template, context: Context):
    """
    TODO: Describe
    """
    if 'name' in template:
        t_name = template['name']
        name = t.walk(t_name, context)
        return context.this[name]
    elif 'names' in template:
        t_names = template['names']
        names = t.walk(t_names, context)
        return reduce(operator.getitem, names, context.this)
    else:
        raise DefinitionError('either `name` of `names` attribute is required for `attr` rule')


@Transformer.register_rule(
    'object',
    key="TODO: Describe",  # TODO: Describe
    value="TODO: Describe",  # TODO: Describe
)
def rule_object(t: Transformer, template, context: Context):
    """
    TODO: Describe
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


@Transformer.register_rule(
    'map',
    item="TODO: Describe",  # TODO: Describe
    items="TODO: Describe",  # TODO: Describe
    key="TODO: Describe",  # TODO: Describe
    value="TODO: Describe",  # TODO: Describe
)
def rule_map(t: Transformer, template, context: Context):
    """
    TODO: Describe
    """
    def iter_contexts(data):
        if isinstance(data, list):
            for index, _item in enumerate(data):
                yield context.derive(this=_item, index=index, item=_item)
        elif isinstance(data, dict):
            for index, (_key, _value) in enumerate(data.items()):
                yield context.derive(this=_value, index=index, key=_key, value=_value)

    if 'item' in template:
        t_item = template['item']
        result = []
        for sub_context in iter_contexts(context.this):
            item = t.walk(t_item, sub_context)
            if item is t.NO_CONTENT:
                continue
            result.append(item)
        return result
    elif 'items' in template:
        t_items = template['items']
        result = []
        for sub_context in iter_contexts(context.this):
            for item in t.walk(t_items, sub_context):
                if item is t.NO_CONTENT:
                    continue
                result.append(item)
        return result
    elif 'key' in template and 'value' in template:
        t_key = template['key']
        t_value = template['value']
        result = {}
        for sub_context in iter_contexts(context.this):
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
    'zip',
    items="TODO: Describe",  # TODO: Describe
)
def rule_zip(t: Transformer, template, context: Context):
    """
    TODO: Describe
    """
    if 'items' in template:
        t_items = template['items']
        items = t.walk(t_items, context)
        return list(zip(*items))
    raise DefinitionError('`items` attribute is  required for `zip` rule')


@Transformer.register_rule(
    'file',
    name="TODO: Describe",  # TODO: Describe
    content="TODO: Describe",  # TODO: Describe
)
def rule_file(t: Transformer, template, context: Context):
    """
    TODO: Describe
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
    items="TODO: Describe",  # TODO: Describe
    sep="TODO: Describe",  # TODO: Describe
)
def rule_join(t: Transformer, template, context: Context):
    """
    TODO: Describe
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
    funcs="TODO: Describe",  # TODO: Describe
)
def rule_chain(t: Transformer, template, context: Context):
    """
    TODO: Describe
    """
    t_funcs = t.require(template, 'funcs')
    local_context = context
    for t_func in t_funcs:
        value = t.walk(t_func, local_context)
        local_context = local_context.derive(this=value)
    return local_context.this


@Transformer.register_rule(
    'expr',
    op="TODO: Describe",  # TODO: Describe
    value="TODO: Describe",  # TODO: Describe
    values="TODO: Describe",  # TODO: Describe
)
def rule_expr(t: Transformer, template, context: Context):
    """
    TODO: Describe
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
    'convert',
    name="TODO: Describe",  # TODO: Describe
    value="TODO: Describe",  # TODO: Describe
    values="TODO: Describe",  # TODO: Describe
)
def rule_convert(t: Transformer, template, context: Context):
    """
    TODO: Describe
    """
    name = t.require(template, 'name')
    convertor = t.get_convertor(name)

    if 'value' in template:
        t_value = template['value']
        value = t.walk(t_value, context)
        return convertor(value)
    elif 'values' in template:
        t_values = template['values']
        values = t.walk(t_values, context)
        return convertor(*values)
    else:
        return convertor(context.this)


@Transformer.register_rule(
    'format',
    pattern="TODO: Describe",  # TODO: Describe
    value="TODO: Describe",  # TODO: Describe
)
def rule_format(t: Transformer, template, context: Context):
    """
    TODO: Describe
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
