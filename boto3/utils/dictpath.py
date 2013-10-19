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

    >>> path = DictPath(data)
    >>> path.find(data, meta)
    {
        'next': '/?page=3',
        'prev': '/?page=1',
        'count': 64,
    }
    >>> path.find(data, 'object.id')
    7
    >>> path.find(data, 'object.owner_ids')
    [3, 25]
    >>> path.find(data, 'object.properties.type')
    'document'
    >>> path.find(data, 'nonexistent')
    None
    >>> path.find(data, 'nonexistent', retval='Not there')
    'Not there'

"""
from boto3.utils import six


class InvalidPathError(Exception):
    pass


class DictPath(object):
    def __init__(self, data):
        self.data = data

    def find(self, path, data=None, retval=None):
        if not isinstance(path, six.text_type):
            raise InvalidPathError("Path must be a string.")

        if data is None:
            data = self.data

        path_bits = path.split('.', 1)
        key = path_bits[0]

        if not key:
            raise InvalidPathError("An empty path was supplied.")

        found = data.get(key, retval)

        if len(path_bits) == 1:
            return found

        if found is retval:
            return found

        # Recurse to find the rest.
        return self.find(path_bits[1], data=found, retval=retval)

    def store(self, path, value, data=None):
        if not isinstance(path, six.text_type):
            raise InvalidPathError("Path must be a string.")

        path_bits = path.split('.', 1)
        key = path_bits[0]

        if not key:
            raise InvalidPathError("An empty path was supplied.")

        if data is None:
            data = self.data

        if len(path_bits) == 1:
            data[key] = value
            return

        # Make sure it exists.
        sub_data = data.setdefault(key, {})
        return self.store(path_bits[1], value, data=sub_data)
