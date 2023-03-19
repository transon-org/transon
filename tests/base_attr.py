from . import base


class AttrDynamicReferenceName(base.BaseCase):
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': {
            '$': 'attr',
            'name': 'name'
        },
    }
