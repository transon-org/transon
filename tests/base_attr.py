from . import base


class AttrDynamicReferenceName(base.TableDataBaseCase):
    """
    Gets value from input `dict` by the name of attribute defined in different attribute of input data.
    """
    tags = ['attr:name']
    template = {
        '$': 'attr',
        'name': {
            '$': 'attr',
            'name': 'name'
        },
    }
