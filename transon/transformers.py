from typing import (
    Callable,
    Dict,
    NoReturn,
)


class Context:
    def __init__(self, parent=None, **data):
        self._parent = parent
        self._data = data or {}

    def derive(self, **props):
        new_props = {}
        new_props.update(self._data)
        new_props.update(props)
        return Context(self, **new_props)

    @property
    def parent(self):
        return self._parent

    @property
    def this(self):
        return self._data['this']

    @property
    def item(self):
        return self._data['item']

    @property
    def key(self):
        return self._data['key']

    @property
    def value(self):
        return self._data['value']

    @property
    def index(self):
        return self._data['index']

    def __contains__(self, key: str):
        assert key not in ('this', 'item', 'key', 'value', 'index')
        return key in self._data

    def __getitem__(self, key: str):
        assert key not in ('this', 'item', 'key', 'value', 'index')
        return self._data[key]

    def __setitem__(self, key: str, value):
        assert key not in ('this', 'item', 'key', 'value', 'index')
        self._data[key] = value


class DefinitionError(Exception):
    pass


class TransformationError(Exception):
    pass


class NoContent:
    def __getitem__(self, _):
        return self


FileWriterType = Callable[[str, any], NoReturn]
TemplateLoaderType = Callable[[str], 'Transformer']


# noinspection PyUnusedLocal
def no_file_writer(name: str, data):  # pragma: no cover
    return


# noinspection PyUnusedLocal
def no_template_loader(name: str) -> 'Transformer':   # pragma: no cover
    raise RuntimeError(f'template with name `{name}` was not found')


class Transformer:
    """
    ## Usage

    `Transformer` class interpolates template with input data.
    Format of output is defined by template.
    Input is used to fill values into template placeholders.

    ```python
    from transon import Transformer

    transformer = Transformer(template)
    output_data = transformer.transform(input_data)
    ```

    ## Templates

    Template could be any JSON structure. It will be reflected as-is in output, except of `rules` structures.
    Rules are json objects with special attribute named `$` (this is called marker and can be changed).
    If the rule has nested template the same applies to it as well.

    Example template:

    ```json
    {
        "test": {
            "$": "map",
            "item": [
                {
                    "x": {
                        "$": item
                    }
                }
            ]
        }
    }
    ```

    At the top level output will just copy template `{"test": ...}`.
    Then the `map` rule will be applied to the input executing sub-template, defined by `item` attribute,
    for each item in input collection.
    Let's assume that our input is `[1, 2, 3]`.
    Inner template contains another rule `{"$": "item"}` which points to value of items of the input.

    So the final result will be:

    ```json
    {
        "test": [
            [{"x": 1}],
            [{"x": 2}],
            [{"x": 3}],
        ]
    }
    ```

    Note that each item preserves its template definition (including list around object).

    ## Extending

    All rules are pluggable. There is a list of rules available out of the box.
    However, you can easily add your own rules with their own attributes.

    ```python
    @Transformer.register_rule('my_rule')
    def my_rule(t: Transformer, template, context: Context):
        ...
    ```

    You can also inherit `Transformer` class and add rules to subclass to avoid functionality collision.

    ```python
    class Transformer1(Transformer):
        pass

    class Transformer2(Transformer):
        pass

    @Transformer1.register_rule('my_rule')
    def my_rule1(t: Transformer, template, context: Context):
        ...

    @Transformer2.register_rule('my_rule')
    def my_rule2(t: Transformer, template, context: Context):
        ...
    ```

    Note that `my_rule` can be used with both transformers but may behave differently.

    In same fashion you can also add addition operators for expressions (`expr`) calculations
    and function (`call`) using decorators
    `register_operator` and `register_function`.
    """

    DEFAULT_MARKER = '$'
    NO_CONTENT = NoContent()
    _functions: Dict[str, Callable] = {}
    _operators: Dict[str, Callable] = {}
    _rules: Dict[str, Callable] = {}

    @classmethod
    def register_function(cls, name: str):
        def decorator(func):
            cls._functions[name] = func
            return func
        return decorator

    @classmethod
    def register_operator(cls, name: str):
        def decorator(func):
            cls._operators[name] = func
            return func
        return decorator

    @classmethod
    def register_rule(cls, _rule_name: str, **params):
        def decorator(func):
            func.__rule_name__ = _rule_name
            func.__rule_params__ = params
            cls._rules[_rule_name] = func
            return func
        return decorator

    @classmethod
    def get_function(cls, name):
        for c in cls.mro():
            functions = getattr(c, '_functions', {})
            if name in functions:
                return functions[name]
        raise DefinitionError(f'Invalid function `{name}`')

    @classmethod
    def get_operator(cls, name):
        for c in cls.mro():
            operators = getattr(c, '_operators', {})
            if name in operators:
                return operators[name]
        raise DefinitionError(f'Invalid operator `{name}`')

    @classmethod
    def get_rule(cls, name):
        for c in cls.mro():
            rules = getattr(c, '_rules', {})
            if name in rules:
                return rules[name]
        raise DefinitionError(f'Invalid rule `{name}`')

    @classmethod
    def get_rules(cls):
        result = {}
        for c in cls.mro():
            rules = getattr(c, '_rules', {})
            for name, rule in rules.items():
                if name not in result:
                    result[name] = rule
        return list(result.values())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._operators = {}
        cls._rules = {}
        cls._functions = {}

    def __init__(
            self,
            template,
            *,
            file_writer: FileWriterType = no_file_writer,
            template_loader: TemplateLoaderType = no_template_loader,
            marker: str = DEFAULT_MARKER,
    ):
        self.template = template
        self.file_writer = file_writer
        self.template_loader = template_loader
        self.marker = marker

    def walk_list(self, template, context):
        return [
            self.walk(item, context)
            for item in template
        ]
    
    def walk_dict(self, template, context):
        return {
            key: self.walk(value, context)
            for key, value in template.items()
        }

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def walk_scalar(self, template, context):
        return template

    def walk_rule(self, template, context):
        rule_name = template[self.marker]
        rule = self.get_rule(rule_name)
        return rule(self, template, context)

    def walk(self, template, context):
        if isinstance(template, list):
            return self.walk_list(template, context)
        elif isinstance(template, dict):
            if self.marker in template:
                return self.walk_rule(template, context)
            else:
                return self.walk_dict(template, context)
        else:
            return self.walk_scalar(template, context)

    def write_file(self, name, content):
        self.file_writer(name, content)

    def require(self, template, name):
        if name not in template:
            rule = template[self.marker]
            raise DefinitionError(f'`{name}` property is required for `{rule}` rule')
        return template[name]

    def transform(self, data):
        context = Context(this=data)
        return self.walk(self.template, context)
