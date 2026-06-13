from unittest.mock import (
    Mock,
    call,
)

from transon import Transformer

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


def test_write_many_files():
    file_writer = Mock()
    transformer = Transformer({
        '$': 'map',
        'item': {
            '$': 'file',
            'name': {
                '$': 'join',
                'items': [
                    'file_name_',
                    {
                        '$': 'call',
                        'name': 'str',
                        'value': {'$': 'index'}
                    },
                    '.json',
                ]
            },
            'content': {'$': 'item'}
        }
    }, file_writer=file_writer)
    assert transformer.transform([
        {'a': 1},
        ['b', 2],
        'c',
        {'$': 'this'}
    ]) == []
    assert file_writer.call_args_list == [
        call('file_name_0.json', {'a': 1}),
        call('file_name_1.json', ['b', 2]),
        call('file_name_2.json', 'c'),
        call('file_name_3.json', {'$': 'this'}),
    ]


def test_write_single_file():
    file_writer = Mock()
    transformer = Transformer({
        '$': 'file',
        'name': {'$': 'attr', 'name': 'filename'},
        'content': {'$': 'attr', 'name': 'content'}
    }, file_writer=file_writer)
    transformer.transform({'filename': 'test.json', 'content': 'my-data'})
    assert file_writer.call_args_list == [
        call('test.json', 'my-data')
    ]


def test_file_no_name():
    file_writer = Mock()
    transformer = Transformer({
        '$': 'file',
        'name': {'$': 'get', 'name': 'foo'},
        'content': 'bar'
    }, file_writer=file_writer)
    transformer.transform({})
    assert file_writer.call_args_list == []


def test_file_no_content():
    file_writer = Mock()
    transformer = Transformer({
        '$': 'file',
        'name': 'foo',
        'content': {'$': 'get', 'name': 'bar'},
    }, file_writer=file_writer)
    transformer.transform({})
    assert file_writer.call_args_list == []
