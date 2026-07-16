from . import base


class B64Encode(base.TableDataBaseCase):
    """
    Encodes a UTF-8 string as standard-alphabet base64 with `b64encode`.
    """
    tags = ['call', 'func:b64encode']
    template = {'$': 'call', 'name': 'b64encode'}
    data = 'hi'
    result = 'aGk='


class B64Decode(base.TableDataBaseCase):
    """
    Decodes standard-alphabet base64 to a UTF-8 string with `b64decode`.
    """
    tags = ['call', 'func:b64decode']
    template = {'$': 'call', 'name': 'b64decode'}
    data = 'aGk='
    result = 'hi'


class Uuid5Dns(base.TableDataBaseCase):
    """
    Builds a deterministic UUID5 from a well-known namespace and a name.
    """
    tags = ['call:values', 'func:uuid5']
    template = {
        '$': 'call',
        'name': 'uuid5',
        'values': ['dns', 'example.com'],
    }
    data = None
    result = 'cfbff0d1-9375-5685-968c-48ce8b15ae17'


class RegexMatchGroups(base.TableDataBaseCase):
    """
    Returns capture groups from `regex_match` on a successful match.
    """
    tags = ['call:values', 'func:regex_match']
    template = {
        '$': 'call',
        'name': 'regex_match',
        'values': [{'$': 'this'}, r'(\w+)@(\w+)'],
    }
    data = 'user@host'
    result = ['user', 'host']


class RegexMatchNone(base.TableDataBaseCase):
    """
    Returns `null` from `regex_match` when the pattern does not match.
    """
    tags = ['call:values', 'func:regex_match']
    template = {
        '$': 'call',
        'name': 'regex_match',
        'values': [{'$': 'this'}, r'^\d+$'],
    }
    data = 'abc'
    result = None


class RegexReplace(base.TableDataBaseCase):
    """
    Replaces regex matches with `regex_replace`.
    """
    tags = ['call:values', 'func:regex_replace']
    template = {
        '$': 'call',
        'name': 'regex_replace',
        'values': [{'$': 'this'}, r'\d+', '#'],
    }
    data = 'a1b22c'
    result = 'a#b#c'
