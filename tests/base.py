import unittest

from transon import Transformer


class BaseCase(unittest.TestCase):
    template = None
    data = None
    result = None
    tags = []

    def test(self):
        if self.template is None:
            self.skipTest("no template")
        if self.data is None:
            self.skipTest("no data")
        if self.result is None:
            self.skipTest("no result")

        assert self.tags

        transformer = Transformer(self.template)
        assert transformer.transform(self.data) == self.result
