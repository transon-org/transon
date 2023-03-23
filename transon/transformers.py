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


# noinspection PyUnusedLocal
def no_file_writer(name, data):  # pragma: no cover
    return


class Transformer:
    DEFAULT_MARKER = '$'
    NO_CONTENT = NoContent()
    _convertors: Dict[str, Callable] = {}
    _operators: Dict[str, Callable] = {}
    _rules = {}

    @classmethod
    def register_convertor(cls, name: str):
        def decorator(func):
            cls._convertors[name] = func
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
    def get_convertor(cls, name):
        for c in cls.mro():
            convertor = getattr(c, '_convertors', {})
            if name in convertor:
                return convertor[name]
        raise DefinitionError(f'Invalid convertor `{name}`')

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
        cls._convertors = {}

    def __init__(self, template, *, file_writer: FileWriterType = no_file_writer, marker: str = DEFAULT_MARKER):
        self.template = template
        self.file_writer = file_writer
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
        result = self.walk(self.template, context)
        if result is self.NO_CONTENT:
            return None
        return result
