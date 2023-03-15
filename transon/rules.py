from functools import reduce

from transon import (
    Transformer,
    Context,
    TransformationError,
    DefinitionError,
)


@Transformer.register_rule('this')
def rule_this(t: Transformer, template, context: Context):
    return context.this


@Transformer.register_rule('parent')
def rule_parent(t: Transformer, template, context: Context):
    return context.parent.this


@Transformer.register_rule('item')
def rule_item(t: Transformer, template, context: Context):
    return context.item


@Transformer.register_rule('key')
def rule_key(t: Transformer, template, context: Context):
    return context.key


@Transformer.register_rule('index')
def rule_index(t: Transformer, template, context: Context):
    return context.index


@Transformer.register_rule('value')
def rule_value(t: Transformer, template, context: Context):
    return context.value


@Transformer.register_rule('attr')
def rule_attr(t: Transformer, template, context: Context):
    if 'name' not in template:
        raise DefinitionError('`name` property is required for `attr` rule')
    t_name = template['name']
    name = t.walk(t_name, context)
    return context.this[name]


@Transformer.register_rule('object')
def rule_object(t: Transformer, template, context: Context):
    t_key = template['key']
    t_value = template['value']
    key = t.walk(t_key, context)
    value = t.walk(t_value, context)
    if key is t.NOCONTENT:
        return {}
    if value is t.NOCONTENT:
        return {}
    return {key: value}


@Transformer.register_rule('map')
def rule_map(t: Transformer, template, context: Context):
    def iter_contexts(data):
        if isinstance(data, list):
            for index, item in enumerate(data):
                yield context.derive(this=item, index=index, item=item)
        elif isinstance(data, dict):
            for index, (key, value) in enumerate(data.items()):
                yield context.derive(this=value, index=index, key=key, value=value)

    if 'item' in template:
        t_item = template['item']
        result = []
        for sub_context in iter_contexts(context.this):
            item = t.walk(t_item, sub_context)
            if item is t.NOCONTENT:
                continue
            result.append(item)
        return result
    elif 'items' in template:
        t_items = template['items']
        result = []
        for sub_context in iter_contexts(context.this):
            for item in t.walk(t_items, sub_context):
                if item is t.NOCONTENT:
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
            if key is t.NOCONTENT:
                continue
            if value is t.NOCONTENT:
                continue
            result[key] = value
        return result

    raise DefinitionError(
        'either `item` or `items` or `key/value` properties '
        'are required for `map` rule'
    )


@Transformer.register_rule('file')
def rule_file(t: Transformer, template, context: Context):
    def write_file(_name, _content):
        if _name is t.NOCONTENT:
            return
        if _content is t.NOCONTENT:
            return
        t.write_file(_name, _content)

    t_name = template['name']
    t_content = template['content']
    name = t.walk(t_name, context)
    content = t.walk(t_content, context)
    write_file(name, content)
    return t.NOCONTENT


def _is_str(x):
    return isinstance(x, str)


def _is_list(x):
    return isinstance(x, list)


def _is_dict(x):
    return isinstance(x, dict)


@Transformer.register_rule('join')
def rule_join(t: Transformer, template, context: Context):
    t_items = template['items']
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


@Transformer.register_rule('chain')
def rule_chain(t: Transformer, template, context: Context):
    t_funcs = template['funcs']
    local_context = context
    for t_func in t_funcs:
        value = t.walk(t_func, local_context)
        local_context = local_context.derive(this=value)
    return local_context.this


@Transformer.register_rule('expr')
def rule_expr(t: Transformer, template, context: Context):
    op_code = template['op']
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


@Transformer.register_rule('convert')
def rule_convert(t: Transformer, template, context: Context):
    name = template['name']
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
