import unittest

from transon import Transformer


class TableDataBaseCase(unittest.TestCase):
    """
    TBD: This is base class for all test cases with table data.
    """
    _test_cases = []
    template = None
    data = None
    result = None
    tags = []

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
        if cls.template is None:
            raise unittest.SkipTest("no template")
        if cls.data is None:
            raise unittest.SkipTest("no data")
        if cls.result is None:
            raise unittest.SkipTest("no result")

    def test(self):
        self.is_valid()
        assert self.tags

        transformer = Transformer(self.template)
        assert transformer.transform(self.data) == self.result
