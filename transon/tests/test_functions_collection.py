from . import base


class LengthOfString(base.TableDataBaseCase):
    """
    Returns the length of a string with `length`.
    """
    tags = ['call', 'func:length']
    template = {'$': 'call', 'name': 'length'}
    data = 'hello'
    result = 5


class LengthOfArray(base.TableDataBaseCase):
    """
    Returns the length of an array with `length`.
    """
    tags = ['call', 'func:length']
    template = {'$': 'call', 'name': 'length'}
    data = [1, 2, 3]
    result = 3


class FlattenOneLevel(base.TableDataBaseCase):
    """
    Flattens one level of an array-of-arrays with `flatten`.
    """
    tags = ['call', 'func:flatten']
    template = {'$': 'call', 'name': 'flatten'}
    data = [[1, 2], [3], [4, 5]]
    result = [1, 2, 3, 4, 5]


class SumNumbers(base.TableDataBaseCase):
    """
    Sums an array of numbers with `sum` (`sum([])` is `0`).
    """
    tags = ['call', 'func:sum']
    template = {'$': 'call', 'name': 'sum'}
    data = [1, 2, 3.5]
    result = 6.5


class MinOfArray(base.TableDataBaseCase):
    """
    Returns the minimum element of an array with `min`.
    """
    tags = ['call:values', 'func:min']
    template = {
        '$': 'call',
        'name': 'min',
        'values': [{'$': 'this'}],
    }
    data = [3, 1, 2]
    result = 1


class MaxWithDefault(base.TableDataBaseCase):
    """
    Returns the provided default when `max` is called on an empty array.
    """
    tags = ['call:values', 'func:max']
    template = {
        '$': 'call',
        'name': 'max',
        'values': [{'$': 'this'}, 0],
    }
    data = []
    result = 0


class SortedArray(base.TableDataBaseCase):
    """
    Returns a new ascending-sorted array of homogeneous scalars with `sorted`.
    """
    tags = ['call', 'func:sorted']
    template = {'$': 'call', 'name': 'sorted'}
    data = [3, 1, 2]
    result = [1, 2, 3]


class UniquePreserveOrder(base.TableDataBaseCase):
    """
    Deduplicates an array while preserving first-occurrence order with `unique`.
    """
    tags = ['call', 'func:unique']
    template = {'$': 'call', 'name': 'unique'}
    data = ['a', 'b', 'a', 'c', 'b']
    result = ['a', 'b', 'c']


class AbsNumber(base.TableDataBaseCase):
    """
    Returns the absolute value of a number with `abs`.
    """
    tags = ['call', 'func:abs']
    template = {'$': 'call', 'name': 'abs'}
    data = -7
    result = 7


class FloorNumber(base.TableDataBaseCase):
    """
    Returns the floor of a number with `floor`.
    """
    tags = ['call', 'func:floor']
    template = {'$': 'call', 'name': 'floor'}
    data = 3.7
    result = 3


class CeilNumber(base.TableDataBaseCase):
    """
    Returns the ceiling of a number with `ceil`.
    """
    tags = ['call', 'func:ceil']
    template = {'$': 'call', 'name': 'ceil'}
    data = 3.2
    result = 4


class RoundWithDigits(base.TableDataBaseCase):
    """
    Rounds a number to a given number of digits with `round`.
    """
    tags = ['call:values', 'func:round']
    template = {
        '$': 'call',
        'name': 'round',
        'values': [{'$': 'this'}, 2],
    }
    data = 3.14159
    result = 3.14


class BoolOfNull(base.TableDataBaseCase):
    """
    Converts a value to a boolean by Python truthiness with `bool` (total).
    """
    tags = ['call', 'func:bool']
    template = {'$': 'call', 'name': 'bool'}
    data = None
    result = False
