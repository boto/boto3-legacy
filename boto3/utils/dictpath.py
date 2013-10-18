"""
dictpath
========

Given an arbitrary ``dict`` & a string path, fetches the data out of the
dictionary.

Given the following data...::

    >>> data = {
    ...     'object': {
    ...         'id': 7,
    ...         'name': 'test',
    ...         'owner_ids': [
    ...             3,
    ...             25,
    ...         ],
    ...         'properties': {
    ...             'type': 'document',
    ...             'created': datetime.datetime(2013, 10, 18, 15, 16, 12),
    ...             'perms': [
    ...                 {'who': 'owner', 'access': 'read'},
    ...                 {'who': 'owner', 'access': 'edit'},
                        {'who': 'owner', 'access': 'delete'},
                        {'who': 'anyone', 'access': 'read'},
    ...             ]
    ...         }
    ...     },
    ...     'meta': {
    ...         'next': '/?page=3',
    ...         'prev': '/?page=1',
    ...         'count': 64,
    ...     }
    ... }

...some examples of usage look like::

    >>> dictpath(data, meta)
    {
        'next': '/?page=3',
        'prev': '/?page=1',
        'count': 64,
    }
    >>> dictpath(data, 'object.id')
    7
    >>> dictpath(data, 'object.owner_ids')
    [3, 25]
    >>> dictpath(data, 'object.properties.type')
    'document'
    >>> dictpath(data, 'nonexistent')
    None
    >>> dictpath(data, 'nonexistent', retval='Not there')
    'Not there'

"""
from boto3.utils import six


class InvalidPathError(Exception):
    pass


def dictpath(data, path, retval=None):
    if not isinstance(path, six.text_type):
        raise InvalidPathError("Path must be a string.")

    path_bits = path.split('.', 1)
    key = path_bits[0]

    if not key:
        raise InvalidPathError("An empty path was supplied.")

    found = data.get(path_bits[0], retval)

    if len(path_bits) == 1:
        return found

    if found is retval:
        return found

    # Recurse to find the rest.
    return dictpath(found, path_bits[1])
