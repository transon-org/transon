from unittest.mock import (
    Mock,
    call,
)

from transon import (
    Transformer,
)


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
