import unittest
from typing import List

from transon import Transformer


undefined = object()


class TableDataBaseCase(unittest.TestCase):
    """
    TBD: This is base class for all test cases with table data.
    """
    _test_cases = []
    template = undefined
    data = undefined
    result = undefined
    tags: List[str] = None

    @classmethod
    def iterate_valid_cases(cls):
        for case in cls._test_cases:
            try:
                case.is_valid()
            except unittest.SkipTest:
                pass
            else:
                yield case

    def __init_subclass__(cls, **kwargs):
        cls._test_cases.append(cls)

    @classmethod
    def is_valid(cls):
        if cls.template is undefined:
            raise unittest.SkipTest("no template")
        if cls.data is undefined:
            raise unittest.SkipTest("no data")
        if cls.result is undefined:
            raise unittest.SkipTest("no result")

    def template_loader(self, name: str):
        from transon.docs import template_loader
        return template_loader(name)

    def test(self):
        self.is_valid()
        assert self.tags is not None

        transformer = Transformer(
            self.template,
            template_loader=self.template_loader,
        )
        output = transformer.transform(self.data)
        if output is transformer.NO_CONTENT:
            output = None
        assert output == self.result


class ErrorBaseCase(unittest.TestCase):
    """
    Base class for error-model example cases.

    Each subclass pairs a template (and, for `transform` cases, input data) with the
    *exact* located, typed error transon raises for it — including the
    ``at template → …`` location line. The test asserts the full message, so the
    error text published on the docs site can never drift from the engine. Harvested
    into the docs `errors` block by `transon.docs`.
    """
    _error_cases: List[type] = []
    template = undefined
    data = undefined
    error = undefined
    error_type = undefined
    action = 'transform'
    tags: List[str] = ['error']

    _ERROR_TYPES = ('DefinitionError', 'TransformationError')

    @classmethod
    def iterate_valid_cases(cls):
        for case in cls._error_cases:
            try:
                case.is_valid()
            except unittest.SkipTest:
                pass
            else:
                yield case

    def __init_subclass__(cls, **kwargs):
        cls._error_cases.append(cls)

    @classmethod
    def is_valid(cls):
        if cls.template is undefined:
            raise unittest.SkipTest("no template")
        if cls.error is undefined:
            raise unittest.SkipTest("no error")
        if cls.error_type not in cls._ERROR_TYPES:
            raise unittest.SkipTest("no error_type")
        if cls.action == 'transform' and cls.data is undefined:
            raise unittest.SkipTest("no data")

    def template_loader(self, name: str):
        from transon.docs import template_loader
        return template_loader(name)

    def test(self):
        self.is_valid()
        assert self.tags is not None

        from transon import DefinitionError, TransformationError
        error_classes = {
            'DefinitionError': DefinitionError,
            'TransformationError': TransformationError,
        }
        expected = error_classes[self.error_type]

        transformer = Transformer(
            self.template,
            template_loader=self.template_loader,
        )
        with self.assertRaises(expected) as ctx:
            if self.action == 'validate':
                transformer.validate()
            else:
                transformer.transform(self.data)

        message = str(ctx.exception)
        assert message == self.error, (
            f'{type(self).__name__}: expected error message {self.error!r}, '
            f'got {message!r}'
        )
