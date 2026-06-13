import contextvars
import copy
from typing import (
    Any,
    Callable,
    Dict,
    Tuple,
)

_template_path: contextvars.ContextVar[Tuple[str, ...]] = contextvars.ContextVar(
    'transon_template_path',
    default=(),
)


def format_error_message(message: str) -> str:
    path = _template_path.get()
    if not path:
        return message
    location = ' → '.join(('template',) + path)
    return f'{message}\n  at {location}'


class DefinitionError(Exception):
    pass


class TransformationError(Exception):
    pass


class Context:
    RESERVED_NAMES = ('this', 'item', 'key', 'value', 'index')

    def __init__(self, parent=None, **data):
        self._parent = parent
        self._data = data or {}
        self._materialized = parent is None

    def derive(self, **props):
        return Context(self, **props)

    def _materialize_from_parent(self):
        if self._materialized or self._parent is None:
            return
        merged = {}
        chain = []
        ctx = self._parent
        while ctx is not None:
            chain.append(ctx)
            ctx = ctx._parent
        for ctx in reversed(chain):
            merged.update(ctx._data)
        for key, value in merged.items():
            if key not in self._data:
                self._data[key] = value
        self._materialized = True

    @property
    def parent(self):
        return self._parent

    @property
    def this(self):
        return self._data['this']

    def _require_slot(self, name, message):
        ctx = self
        while ctx is not None:
            if name in ctx._data:
                return ctx._data[name]
            ctx = ctx._parent
        raise DefinitionError(format_error_message(message))

    @property
    def item(self):
        return self._require_slot(
            'item',
            '`item` is only valid inside `map`/`filter` over a list',
        )

    @property
    def key(self):
        return self._require_slot(
            'key',
            '`key` is only valid inside `map`/`filter` over a dict',
        )

    @property
    def value(self):
        return self._require_slot(
            'value',
            '`value` is only valid inside `map`/`filter` over a dict',
        )

    @property
    def index(self):
        return self._require_slot(
            'index',
            '`index` is only valid inside `map`/`filter`',
        )

    @classmethod
    def _check_not_reserved(cls, key: str):
        if key in cls.RESERVED_NAMES:
            raise DefinitionError(format_error_message(
                f'`{key}` is a reserved name and cannot be used as a variable name'
            ))

    def __contains__(self, key: str):
        self._check_not_reserved(key)
        if key in self._data:
            return True
        if self._parent is not None:
            return key in self._parent
        return False

    def __getitem__(self, key: str):
        self._check_not_reserved(key)
        if key in self._data:
            return self._data[key]
        if self._parent is not None:
            return self._parent[key]
        raise KeyError(key)

    def __setitem__(self, key: str, value):
        self._check_not_reserved(key)
        if not self._materialized:
            self._materialize_from_parent()
        self._data[key] = value


class NoContent:
    def __getitem__(self, _):
        return self

    def __bool__(self):
        return False


FileWriterType = Callable[[str, Any], None]
TemplateLoaderType = Callable[[str], 'Transformer']

DEFAULT_MAX_INCLUDE_DEPTH = 50


# noinspection PyUnusedLocal
def no_file_writer(name: str, data):  # pragma: no cover
    return


# noinspection PyUnusedLocal
def no_template_loader(name: str) -> 'Transformer':   # pragma: no cover
    raise DefinitionError(format_error_message(
        f'template with name `{name}` was not found'
    ))


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

    Template could be any JSON structure. It will be reflected as-is in output, except for rule structures.
    Rules are JSON objects with special attribute named `$` (this is called marker and can be changed).
    If the rule has nested template the same applies to it as well.

    Example template:

    ```json
    {
        "test": {
            "$": "map",
            "item": [
                {
                    "x": {
                        "$": "item"
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
            [{"x": 3}]
        ]
    }
    ```

    Note that each item preserves its template definition (including list around object).

    ## Extending

    All rules are pluggable. Built-in rules are documented below under **Rules**.
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

    In the same fashion you can also add additional operators for expressions (`expr`) calculations
    and functions (`call`) using decorators
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
    def register_rule(cls, _rule_name: str, *, _required=(), _modes=(), **params):
        def decorator(func):
            func.__rule_name__ = _rule_name
            func.__rule_params__ = params
            func.__rule_schema__ = {
                'required': tuple(_required),
                'modes': tuple(tuple(mode) for mode in _modes),
            }
            cls._rules[_rule_name] = func
            return func
        return decorator

    @classmethod
    def get_function(cls, name):
        for c in cls.mro():
            functions = getattr(c, '_functions', {})
            if name in functions:
                return functions[name]
        raise DefinitionError(format_error_message(f'Invalid function `{name}`'))

    @classmethod
    def get_operator(cls, name):
        for c in cls.mro():
            operators = getattr(c, '_operators', {})
            if name in operators:
                return operators[name]
        raise DefinitionError(format_error_message(f'Invalid operator `{name}`'))

    @classmethod
    def get_rule(cls, name):
        for c in cls.mro():
            rules = getattr(c, '_rules', {})
            if name in rules:
                return rules[name]
        raise DefinitionError(format_error_message(f'Invalid rule `{name}`'))

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
            validate: bool = False,
            file_writer: FileWriterType = no_file_writer,
            template_loader: TemplateLoaderType = no_template_loader,
            marker: str = DEFAULT_MARKER,
            max_include_depth: int = DEFAULT_MAX_INCLUDE_DEPTH,
    ):
        self.template = template
        self.file_writer = file_writer
        self.template_loader = template_loader
        self.marker = marker
        self.max_include_depth = max_include_depth
        self._include_stack = []
        if validate:
            self.validate()

    @property
    def path(self) -> Tuple[str, ...]:
        return _template_path.get()

    def definition_error(self, message: str) -> None:
        raise DefinitionError(format_error_message(message))

    def transformation_error(self, message: str) -> None:
        raise TransformationError(format_error_message(message))

    def walk_param(self, param_template, context, param_name: str):
        return self.walk(param_template, context, self.path + (param_name,))

    def _walk_with_path(self, path: Tuple[str, ...], func):
        token = _template_path.set(path)
        try:
            return func()
        finally:
            _template_path.reset(token)

    def walk_list(self, template, context, path):
        return [
            self.walk(item, context, path + (f'[{index}]',))
            for index, item in enumerate(template)
        ]

    def walk_dict(self, template, context, path):
        return {
            key: self.walk(value, context, path + (key,))
            for key, value in template.items()
        }

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def walk_scalar(self, template, context, path):
        return template

    def walk_rule(self, template, context, path):
        rule_name = template[self.marker]
        rule_path = path + (rule_name,)
        return self._walk_with_path(
            rule_path,
            lambda: self.get_rule(rule_name)(self, template, context),
        )

    def walk(self, template, context, path=()):
        return self._walk_with_path(path, lambda: self._walk(template, context, path))

    def _walk(self, template, context, path):
        if isinstance(template, list):
            return self.walk_list(template, context, path)
        if isinstance(template, dict):
            if self.marker in template:
                return self.walk_rule(template, context, path)
            return self.walk_dict(template, context, path)
        return self.walk_scalar(template, context, path)

    def write_file(self, name, content):
        self.file_writer(name, content)

    def require(self, template, name):
        if name not in template:
            rule = template[self.marker]
            self.definition_error(
                f'`{name}` property is required for `{rule}` rule'
            )
        return template[name]

    def validate(self):
        """Validate the template statically without input data."""
        self._walk_with_path((), lambda: self._validate_template(self.template))

    def _validate_template(self, template, path=()):
        if isinstance(template, list):
            for index, item in enumerate(template):
                self._validate_template(item, path + (f'[{index}]',))
        elif isinstance(template, dict):
            if self.marker in template:
                self._validate_rule(template, path)
            else:
                for key, value in template.items():
                    self._validate_template(value, path + (key,))

    def _validate_rule(self, template, path):
        rule_name = template[self.marker]
        rule_path = path + (rule_name,)

        def validate_body():
            rule = self.get_rule(rule_name)
            self._validate_rule_params(rule_name, rule, template)
            self._validate_rule_constants(rule_name, template)
            for key, value in template.items():
                if key == self.marker:
                    continue
                if (
                    rule_name == 'object'
                    and key == 'fields'
                    and isinstance(value, dict)
                ):
                    for field_key, field_value in value.items():
                        self._validate_template(
                            field_value, rule_path + (key, field_key)
                        )
                else:
                    self._validate_template(value, rule_path + (key,))

        self._walk_with_path(rule_path, validate_body)

    def _validate_rule_params(self, rule_name, rule, template):
        known = set(getattr(rule, '__rule_params__', {}))
        present = {key for key in template if key != self.marker}
        unknown = present - known
        if unknown:
            names = ', '.join(f'`{name}`' for name in sorted(unknown))
            self.definition_error(
                f'unknown {names} for `{rule_name}` rule'
            )

        schema = getattr(rule, '__rule_schema__', {})
        for param in schema.get('required', ()):
            if param not in present:
                self.definition_error(
                    f'`{param}` property is required for `{rule_name}` rule'
                )

        modes = schema.get('modes', ())
        if modes:
            self._validate_rule_modes(rule_name, present, modes)

    def _validate_rule_modes(self, rule_name, present, modes):
        mode_sets = [frozenset(mode) for mode in modes]
        all_mode_params = set().union(*mode_sets) if mode_sets else set()
        non_empty_modes = [mode for mode in mode_sets if mode]
        has_empty_mode = any(not mode for mode in mode_sets)

        active_modes = [mode for mode in non_empty_modes if mode <= present]
        for mode in non_empty_modes:
            if mode & present and not mode <= present:
                missing = sorted(mode - present)
                self.definition_error(
                    f'incomplete parameter set {sorted(mode)!r} for '
                    f'`{rule_name}` rule (missing {missing!r})'
                )

        if len(active_modes) > 1:
            params = sorted(set().union(*active_modes))
            self.definition_error(
                f'ambiguous mutually exclusive parameters for `{rule_name}` rule: '
                f'{params!r}'
            )

        if active_modes:
            return

        if has_empty_mode and not (present & all_mode_params):
            return

        self.definition_error(
            f'no valid parameter combination for `{rule_name}` rule'
        )

    def _validate_rule_constants(self, rule_name, template):
        if rule_name == 'expr' and 'op' in template:
            op = template['op']
            if isinstance(op, str):
                self.get_operator(op)
        elif rule_name == 'call' and 'name' in template:
            name = template['name']
            if isinstance(name, str):
                self.get_function(name)
        elif rule_name == 'chain' and 'funcs' in template:
            funcs = template['funcs']
            if not isinstance(funcs, list):
                self.definition_error(
                    '`funcs` must be a list for `chain` rule'
                )

    def _prepare_include(self, name):
        stack = list(self._include_stack)
        stack.append(name)
        if len(stack) > self.max_include_depth:
            chain = ' → '.join(stack)
            self.transformation_error(
                'include depth limit ({0}) exceeded: {1}'.format(
                    self.max_include_depth,
                    chain,
                )
            )
        return stack

    def transform(self, data, no_content=None, *, copy_output: bool = False):
        """
        Transform ``data`` with this transformer's template.

        ``no_content`` controls the value returned when the template evaluates to
        ``NO_CONTENT`` (defaults to ``None``; pass ``Transformer.NO_CONTENT`` to
        receive the raw sentinel).

        Output aliasing: ``transform()`` never mutates the input data or the template,
        but rules that pass values straight through (e.g. ``this``, ``attr``, ``get``,
        ``item``) return *references* into the input. Mutating the returned structure
        afterwards therefore mutates the original input. Pass ``copy_output=True`` to
        deep-copy the result once at this boundary, yielding a value that shares no
        mutable structure with the input.
        """
        context = Context(this=data)
        result = self.walk(self.template, context)
        if result is self.NO_CONTENT and no_content is not self.NO_CONTENT:
            return no_content
        if copy_output:
            return copy.deepcopy(result)
        return result
