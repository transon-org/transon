from . import base


class FileWriteViaMap(base.TableDataBaseCase):
    """
    The ``file`` rule writes output through a ``file_writer`` delegate passed to
    ``Transformer(...)``. It always returns ``NO_CONTENT`` (shown as ``null`` in JSON),
    so ``map`` over it yields an empty list — the side effect is the write, not the
    transform result. ``name`` and ``content`` are templates; if either evaluates to
    ``NO_CONTENT``, nothing is written for that invocation.
    """
    tags = ['file', 'file:name', 'file:content']
    template = {
        '$': 'map',
        'item': {
            '$': 'file',
            'name': {
                '$': 'join',
                'items': [
                    'output_',
                    {
                        '$': 'call',
                        'name': 'str',
                        'value': {'$': 'index'},
                    },
                    '.json',
                ],
            },
            'content': {'$': 'item'},
        },
    }
    data = [
        {'id': 1},
        {'id': 2},
    ]
    result = []
