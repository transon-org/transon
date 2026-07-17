import contextvars
import copy
import dataclasses
import enum
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
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
# `include` always calls the loader as ``loader(name, context=IncludeContext)``; the
# ``context`` is optional so a loader may also be invoked standalone.
TemplateLoaderType = Callable[..., 'Transformer']

DEFAULT_MAX_INCLUDE_DEPTH = 50


# noinspection PyUnusedLocal
def no_file_writer(name: str, data):  # pragma: no cover
    return


# noinspection PyUnusedLocal
def no_template_loader(name: str, context=None) -> 'Transformer':   # pragma: no cover
    raise DefinitionError(format_error_message(
        f'template with name `{name}` was not found'
    ))


class ParamKind(enum.Enum):
    """Whether a rule parameter is a walked template or a verbatim literal."""
    DYNAMIC = 'dynamic'
    CONSTANT = 'constant'


class ContainerType(enum.Enum):
    """How static validation descends into a rule parameter's value.

    - ``TEMPLATE`` — a single sub-template (the default).
    - ``MAPPING`` — an object whose keys are literal and whose values are templates.
    - ``LIST`` — an array of templates.
    - ``ARMS`` — an array of objects whose slots are declared like parameters.
    """
    TEMPLATE = 'template'
    MAPPING = 'mapping'
    LIST = 'list'
    ARMS = 'arms'


class Domain(enum.Enum):
    """Closed enum domain a constant parameter is drawn from."""
    OPERATOR = 'operator'
    FUNCTION = 'function'


@dataclasses.dataclass(frozen=True)
class ParamSpec:
    """Declarative metadata for a single rule parameter (or arm slot)."""
    doc: str = ''
    kind: ParamKind = ParamKind.DYNAMIC
    container: ContainerType = ContainerType.TEMPLATE
    domain: Optional[Domain] = None
    arm: Optional['ArmSpec'] = None


@dataclasses.dataclass(frozen=True)
class ArmSpec:
    """Declarative schema for the objects of an ``ARMS`` container.

    Each arm is validated the **same way** as a rule's parameters: ``params`` maps
    each slot name to its :class:`ParamSpec`, and ``required`` lists the slots every
    arm must provide.
    """
    required: Tuple[str, ...]
    params: Dict[str, ParamSpec]


def _build_param_specs(params, constants, containers, arms):
    specs = {}
    for name, doc in params.items():
        domain = constants.get(name)
        if name in arms:
            container = ContainerType.ARMS
        else:
            container = containers.get(name, ContainerType.TEMPLATE)
        specs[name] = ParamSpec(
            doc=doc,
            kind=ParamKind.CONSTANT if domain is not None else ParamKind.DYNAMIC,
            container=container,
            domain=domain,
            arm=arms.get(name),
        )
    return specs


def arm(*, _variants, _constants=None, _containers=None, **slots) -> ArmSpec:
    """Declare the schema of an ``ARMS`` container's objects.

    Slots are declared the **same way** as rule parameters — slot docstrings as
    keyword arguments plus ``_variants``/``_constants``/``_containers`` — so an arm
    is effectively a small parameter set. The required slots are the intersection
    of the declared variants.
    """
    variant_sets = [frozenset(variant) for variant in _variants]
    required_set = frozenset.intersection(*variant_sets)
    return ArmSpec(
        required=tuple(name for name in slots if name in required_set),
        params=_build_param_specs(
            slots, dict(_constants or {}), dict(_containers or {}), {}
        ),
    )


class Transformer:
    """
    The engine's entry point: construct a `Transformer` from a template (plain
    JSON in which a dict carrying the marker key, default `$`, is a rule
    invocation) and apply it to input data. The **template language** itself —
    the evaluation model, scoping, the `NO_CONTENT` model, the error taxonomy,
    composition patterns — is specified in the
    [Language Reference](https://github.com/transon-org/transon/blob/main/docs/LANGUAGE.md)
    (also served by `transon.reference.get_language_reference()`); what the
    project is and how it compares to alternatives is in the
    [README](https://github.com/transon-org/transon#readme).

    ## Usage

    ```python
    from transon import Transformer

    template = {"items": {"$": "map", "item": {"$": "item"}}}
    Transformer(template).transform(["a", "b"])  # => {"items": ["a", "b"]}
    ```

    Constructor options:

    - **`validate=True`** (or calling `.validate()`) — static template check up
      front, without input data; malformed rules raise `DefinitionError`.
    - **`marker="@"`** — change the rule marker if `$` collides with your data.
    - **`file_writer`** — callback the `file` rule writes through.
    - **`template_loader`** — callback the `include` rule loads sub-templates
      through; it receives an `IncludeContext` and constructs the sub-transformer
      (see :class:`IncludeContext`).
    - **`max_include_depth`** — nested-`include` depth limit (default 50).

    `transform(data, no_content=None, *, copy_output=False)` returns the output:
    `no_content` chooses what a top-level `NO_CONTENT` becomes (default `None`);
    `copy_output=True` deep-copies the result once so it shares no mutable
    structure with the input (which is never mutated regardless — but pass-through
    rules return references into it). Failures raise `DefinitionError` (malformed
    template) or `TransformationError` (data does not fit) — catch these two;
    messages include the template path (`at template → …`).

    ## Extending

    All rules are pluggable, and you can add your own with their own attributes:

    ```python
    @Transformer.register_rule('my_rule')
    def my_rule(t: Transformer, template, context: Context):
        ...
    ```

    You can also inherit `Transformer` and register rules on the subclass to
    avoid functionality collision:

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

    Note that `my_rule` can be used with both transformers but may behave
    differently. In the same fashion you can add operators for `expr` and
    functions for `call` with the `register_operator` and `register_function`
    decorators. Subclass registrations never affect the base class; lookups
    resolve through the MRO (the stability contract is `SPECIFICATION.md` §3).
    """

    DEFAULT_MARKER = '$'
    NO_CONTENT = NoContent()
    _functions: Dict[str, Callable] = {}
    _function_docs: Dict[str, dict] = {}
    _operators: Dict[str, Callable] = {}
    _operator_docs: Dict[str, dict] = {}
    _rules: Dict[str, Callable] = {}

    @classmethod
    def register_function(cls, name: str, *, input_type=None, output_type=None, doc=None):
        def decorator(func):
            cls._functions[name] = func
            if doc is not None:
                cls._function_docs[name] = {
                    'name': name,
                    'input': input_type,
                    'output': output_type,
                    'doc': doc,
                }
            return func
        return decorator

    @classmethod
    def register_operator(cls, name: str, alternative=None, *,
                          kind=None, types=None, result=None, doc=None):
        def decorator(func):
            cls._operators[name] = func
            if alternative is not None:
                cls._operators[alternative] = func
            if doc is not None:
                cls._operator_docs[name] = {
                    'name': name,
                    'alternative': alternative,
                    'kind': kind,
                    'types': types,
                    'result': result,
                    'doc': doc,
                }
            return func
        return decorator

    @classmethod
    def register_rule(
            cls,
            _rule_name: str,
            *,
            _variants=None,
            _constants=None,
            _containers=None,
            _arms=None,
            **params,
    ):
        constants = dict(_constants or {})
        containers = dict(_containers or {})
        arms = dict(_arms or {})
        if _variants is None:
            variants = (frozenset(),)
        else:
            variants = tuple(frozenset(variant) for variant in _variants)

        def decorator(func):
            func.__rule_name__ = _rule_name
            func.__rule_params__ = params
            func.__rule_schema__ = {'variants': variants}
            func.__rule_param_meta__ = _build_param_specs(
                params, constants, containers, arms
            )
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

    @classmethod
    def get_operators(cls):
        result = {}
        for c in cls.mro():
            docs = getattr(c, '_operator_docs', {})
            for name, doc in docs.items():
                if name not in result:
                    result[name] = doc
        return list(result.values())

    @classmethod
    def get_functions(cls):
        result = {}
        for c in cls.mro():
            docs = getattr(c, '_function_docs', {})
            for name, doc in docs.items():
                if name not in result:
                    result[name] = doc
        return list(result.values())

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._operators = {}
        cls._operator_docs = {}
        cls._rules = {}
        cls._functions = {}
        cls._function_docs = {}

    def __init__(
            self,
            template,
            *,
            validate: bool = False,
            file_writer: FileWriterType = no_file_writer,
            template_loader: TemplateLoaderType = no_template_loader,
            marker: str = DEFAULT_MARKER,
            max_include_depth: int = DEFAULT_MAX_INCLUDE_DEPTH,
            include_stack: Optional[Tuple[str, ...]] = None,
    ):
        self.template = template
        self.file_writer = file_writer
        self.template_loader = template_loader
        self.marker = marker
        self.max_include_depth = max_include_depth
        self._include_stack = list(include_stack) if include_stack else []
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

    @contextmanager
    def _walk_with_path(self, path: Tuple[str, ...]):
        token = _template_path.set(path)
        try:
            yield
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
        with self._walk_with_path(rule_path):
            return self.get_rule(rule_name)(self, template, context)

    def walk(self, template, context, path=()):
        # Recursion budget (Roadmap R-32; SPECIFICATION.md "Recursion budget"): one
        # core recursion frame per template node — no `walk`/`_walk` doubling. The
        # template-path `ContextVar` is set inline via `try/finally` rather than a
        # `@contextmanager` generator, so descending one nesting level costs a single
        # stack frame. This is what lets a self-`include`ing template (the editor
        # codec, AD-030) reach depths well past `max_include_depth` before the host
        # call stack overflows — do not reintroduce a per-node wrapper frame here.
        token = _template_path.set(path)
        try:
            if isinstance(template, list):
                return self.walk_list(template, context, path)
            if isinstance(template, dict):
                if self.marker in template:
                    return self.walk_rule(template, context, path)
                return self.walk_dict(template, context, path)
            return self.walk_scalar(template, context, path)
        finally:
            _template_path.reset(token)

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
        with self._walk_with_path(()):
            self._validate_template(self.template)

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

        with self._walk_with_path(rule_path):
            rule = self.get_rule(rule_name)
            self._validate_rule_params(rule_name, rule, template)
            specs = getattr(rule, '__rule_param_meta__', {})
            for key, value in template.items():
                if key == self.marker:
                    continue
                self._validate_param_value(
                    rule_name, key, value, specs[key], rule_path
                )

    def _validate_param_value(self, owner, key, value, spec, path):
        param_path = path + (key,)
        if spec.domain is not None:
            self._validate_constant_domain(value, spec.domain)
        elif spec.container is ContainerType.TEMPLATE:
            self._validate_template(value, param_path)
        elif spec.container is ContainerType.MAPPING:
            if not isinstance(value, dict):
                self.definition_error(
                    f'`{key}` must be a mapping for `{owner}` rule'
                )
            for entry_key, entry_value in value.items():
                self._validate_template(entry_value, param_path + (entry_key,))
        elif spec.container is ContainerType.LIST:
            if not isinstance(value, list):
                self.definition_error(
                    f'`{key}` must be a list for `{owner}` rule'
                )
            for index, item in enumerate(value):
                self._validate_template(item, param_path + (f'[{index}]',))
        elif spec.container is ContainerType.ARMS:
            self._check_arms(owner, key, value, spec.arm)
            for index, arm_value in enumerate(value):
                arm_path = param_path + (f'[{index}]',)
                for slot, slot_spec in spec.arm.params.items():
                    if slot in arm_value:
                        self._validate_param_value(
                            owner, slot, arm_value[slot], slot_spec, arm_path
                        )

    def _check_arms(self, owner, key, value, arm_spec):
        if not isinstance(value, list):
            self.definition_error(
                f'`{key}` must be a list for `{owner}` rule'
            )
        for arm_value in value:
            if (
                not isinstance(arm_value, dict)
                or any(slot not in arm_value for slot in arm_spec.required)
            ):
                slots = ' and '.join(f'`{slot}`' for slot in arm_spec.required)
                self.definition_error(
                    f'each `{key}` arm must include {slots} for `{owner}` rule'
                )

    def iter_arms(self, rule_name, key, value):
        """Validate an ``ARMS`` container and yield ``(index, arm)`` for a rule body.

        Uses the same declarative arm schema as static validation, so the
        malformed-arm error is defined in a single place.
        """
        arm_spec = self.get_rule(rule_name).__rule_param_meta__[key].arm
        self._check_arms(rule_name, key, value, arm_spec)
        for index, arm_value in enumerate(value):
            yield index, arm_value

    def _validate_constant_domain(self, value, domain):
        if not isinstance(value, str):
            return
        if domain is Domain.OPERATOR:
            self.get_operator(value)
        elif domain is Domain.FUNCTION:
            self.get_function(value)

    def _validate_rule_params(self, rule_name, rule, template):
        param_order = list(getattr(rule, '__rule_params__', {}))
        present = {key for key in template if key != self.marker}
        unknown = present - set(param_order)
        if unknown:
            names = ', '.join(f'`{name}`' for name in sorted(unknown))
            self.definition_error(
                f'unknown {names} for `{rule_name}` rule'
            )

        schema = getattr(rule, '__rule_schema__', {})
        variant_sets = list(schema.get('variants', (frozenset(),)))
        required = frozenset.intersection(*variant_sets)
        for param in param_order:
            if param in required and param not in present:
                self.definition_error(
                    f'`{param}` property is required for `{rule_name}` rule'
                )

        modes = tuple(tuple(variant - required) for variant in variant_sets)
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


@dataclasses.dataclass(frozen=True)
class IncludeContext:
    """The parent transformer's include-context, passed to a ``template_loader``.

    ``include`` always calls the loader as ``loader(name, context=IncludeContext)``.
    The loader is responsible for **constructing** the sub-``Transformer`` with these
    inherited settings (marker, depth guard, include-stack, and the parent's loader so
    recursive/self-referential templates re-resolve). Passing the settings in at
    construction — rather than mutating the loaded instance — lets a loader return a
    cached/shared template without leaking one caller's include-state into another.

    Use :meth:`transformer` for the common case, or read the fields directly when
    constructing a ``Transformer`` subclass.
    """
    template_loader: 'TemplateLoaderType'
    marker: str
    max_include_depth: int
    include_stack: Tuple[str, ...] = ()

    def transformer(self, template, *, marker=None, **kwargs):
        """Build a ``Transformer`` for ``template`` carrying this include-context.

        The parent's ``template_loader`` is inherited (so a self-``include`` recurses)
        unless overridden via ``kwargs``. ``marker`` defaults to the parent's marker
        — pass an explicit ``marker`` to pin a different one for the sub-template.
        """
        kwargs.setdefault('template_loader', self.template_loader)
        return Transformer(
            template,
            marker=self.marker if marker is None else marker,
            max_include_depth=self.max_include_depth,
            include_stack=self.include_stack,
            **kwargs,
        )
