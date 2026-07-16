from . import base


class SplitString(base.TableDataBaseCase):
    """
    Splits a string on a separator into a list of strings — the inverse of `join`.
    """
    tags = ['split', 'split:sep']
    template = {'$': 'split', 'sep': '/'}
    data = 'refs/heads/main'
    result = ['refs', 'heads', 'main']


class SplitArrayOnElement(base.TableDataBaseCase):
    """
    Splits an array into sub-arrays on elements equal to `sep`.
    """
    tags = ['split', 'split:sep']
    template = {'$': 'split', 'sep': 0}
    data = [1, 0, 2, 0, 3]
    result = [[1], [2], [3]]


class SplitArrayOnSubsequence(base.TableDataBaseCase):
    """
    Splits an array on each contiguous occurrence of an array `sep` (subsequence).
    """
    tags = ['split', 'split:sep']
    template = {'$': 'split', 'sep': [0, 0]}
    data = [1, 0, 0, 2, 0, 0, 3]
    result = [[1], [2], [3]]
