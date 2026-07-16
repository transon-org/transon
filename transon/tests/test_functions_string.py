from . import base


class UpperString(base.TableDataBaseCase):
    """
    Uppercases a string with the `upper` function.
    """
    tags = ['call', 'func:upper']
    template = {'$': 'call', 'name': 'upper'}
    data = 'usd'
    result = 'USD'


class LowerString(base.TableDataBaseCase):
    """
    Lowercases a string with the `lower` function.
    """
    tags = ['call', 'func:lower']
    template = {'$': 'call', 'name': 'lower'}
    data = 'USD'
    result = 'usd'


class CapitalizeString(base.TableDataBaseCase):
    """
    Capitalizes a string with the `capitalize` function.
    """
    tags = ['call', 'func:capitalize']
    template = {'$': 'call', 'name': 'capitalize'}
    data = 'hello world'
    result = 'Hello world'


class ReplaceSubstring(base.TableDataBaseCase):
    """
    Replaces all occurrences of a substring with `replace`.
    """
    tags = ['call:values', 'func:replace']
    template = {
        '$': 'call',
        'name': 'replace',
        'values': [{'$': 'this'}, 'foo', 'bar'],
    }
    data = 'foo-foo'
    result = 'bar-bar'


class RemovePrefix(base.TableDataBaseCase):
    """
    Removes an exact prefix with `removeprefix` (unlike character-set `lstrip`).
    """
    tags = ['call:values', 'func:removeprefix']
    template = {
        '$': 'call',
        'name': 'removeprefix',
        'values': [{'$': 'this'}, 'refs/heads/'],
    }
    data = 'refs/heads/main'
    result = 'main'


class RemoveSuffix(base.TableDataBaseCase):
    """
    Removes an exact suffix with `removesuffix`.
    """
    tags = ['call:values', 'func:removesuffix']
    template = {
        '$': 'call',
        'name': 'removesuffix',
        'values': [{'$': 'this'}, '.git'],
    }
    data = 'repo.git'
    result = 'repo'


class StripWhitespace(base.TableDataBaseCase):
    """
    Strips leading and trailing whitespace with `strip`.
    """
    tags = ['call', 'func:strip']
    template = {'$': 'call', 'name': 'strip'}
    data = '  hello  '
    result = 'hello'


class LstripChars(base.TableDataBaseCase):
    """
    Strips a leading character set with `lstrip`.
    """
    tags = ['call:values', 'func:lstrip']
    template = {
        '$': 'call',
        'name': 'lstrip',
        'values': [{'$': 'this'}, '0'],
    }
    data = '00123'
    result = '123'


class RstripChars(base.TableDataBaseCase):
    """
    Strips a trailing character set with `rstrip`.
    """
    tags = ['call:values', 'func:rstrip']
    template = {
        '$': 'call',
        'name': 'rstrip',
        'values': [{'$': 'this'}, '0'],
    }
    data = '12300'
    result = '123'


class SliceString(base.TableDataBaseCase):
    """
    Slices a string with `slice` using start and stop indices.
    """
    tags = ['call:values', 'func:slice']
    template = {
        '$': 'call',
        'name': 'slice',
        'values': [{'$': 'this'}, 1, 4],
    }
    data = 'abcdef'
    result = 'bcd'


class SliceArray(base.TableDataBaseCase):
    """
    Slices an array with `slice` from a start index to the end.
    """
    tags = ['call:values', 'func:slice']
    template = {
        '$': 'call',
        'name': 'slice',
        'values': [{'$': 'this'}, 1],
    }
    data = [10, 20, 30, 40]
    result = [20, 30, 40]


class ReversedString(base.TableDataBaseCase):
    """
    Reverses a string with `reversed`.
    """
    tags = ['call', 'func:reversed']
    template = {'$': 'call', 'name': 'reversed'}
    data = 'abc'
    result = 'cba'


class ReversedArray(base.TableDataBaseCase):
    """
    Reverses an array with `reversed`.
    """
    tags = ['call', 'func:reversed']
    template = {'$': 'call', 'name': 'reversed'}
    data = [1, 2, 3]
    result = [3, 2, 1]
