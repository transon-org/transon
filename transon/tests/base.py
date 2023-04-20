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
