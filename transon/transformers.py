from typing import (
    Callable,
    NoReturn,
)


class Context:
    def __init__(self, parent=None, /, **data):
        self._parent = parent
        self._data = data or {}

    def derive(self, **props):
        return Context(self, **(self._data | props))

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
    pass


FileWriterType = Callable[[str, any], NoReturn]


def no_file_writer(name, data):
    return


class Transformer:
    NOCONTENT = NoContent()
    _convertors: dict[str, Callable] = {}
    _operators: dict[str, Callable] = {}
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
    def register_rule(cls, name: str):
        def decorator(func):
            cls._rules[name] = func
            return func
        return decorator

    def get_convertor(self, name):
        for cls in self.__class__.mro():
            convertor = getattr(cls, '_convertors', {})
            if name in convertor:
                return convertor[name]
        raise DefinitionError(f'Invalid convertor `{name}`')

    def get_operator(self, name):
        for cls in self.__class__.mro():
            operators = getattr(cls, '_operators', {})
            if name in operators:
                return operators[name]
        raise DefinitionError(f'Invalid operator `{name}`')

    def get_rule(self, name):
        for cls in self.__class__.mro():
            rules = getattr(cls, '_rules', {})
            if name in rules:
                return rules[name]
        raise DefinitionError(f'Invalid rule `{name}`')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._operators = {}
        cls._rules = {}
        cls._convertors = {}

    def __init__(self, template, *, file_writer: FileWriterType = no_file_writer, marker: str = '$'):
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

    def transform(self, data):
        context = Context(this=data)
        return self.walk(self.template, context)
