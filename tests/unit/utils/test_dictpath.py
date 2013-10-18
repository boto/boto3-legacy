import datetime

from boto3.utils.dictpath import dictpath, InvalidPathError

from tests import unittest


class DictPathTestCase(unittest.TestCase):
    def setUp(self):
        super(DictPathTestCase, self).setUp()
        self.data = {
            'request_id': 'abc123',
            'object': {
                'id': 7,
                'name': 'test',
                'owner_ids': [
                    3,
                    25,
                ],
                'properties': {
                    'type': 'document',
                    'created': datetime.datetime(2013, 10, 18, 15, 16, 12),
                    'perms': [
                        {'who': 'owner', 'access': 'read'},
                        {'who': 'owner', 'access': 'edit'},
                        {'who': 'owner', 'access': 'delete'},
                        {'who': 'anyone', 'access': 'read'},
                    ]
                }
            },
            'meta': {
                'next': '/?page=3',
                'prev': '/?page=1',
                'count': 64,
            }
        }

    def test_simple_data(self):
        selector = 'object.id'
        self.assertEqual(dictpath(self.data, selector), 7)

    def test_fetch_list_data(self):
        selector = 'object.owner_ids'
        self.assertEqual(dictpath(self.data, selector), [3, 25])

    def test_single_key(self):
        selector = 'request_id'
        self.assertEqual(dictpath(self.data, selector), 'abc123')

    def test_single_key_complex_data(self):
        selector = 'meta'
        self.assertEqual(dictpath(self.data, selector), {
            'next': '/?page=3',
            'prev': '/?page=1',
            'count': 64,
        })

    def test_deeper_fetch(self):
        selector = 'object.properties.type'
        self.assertEqual(dictpath(self.data, selector), 'document')

    def test_nonexistent(self):
        selector = 'not-there'
        self.assertEqual(dictpath(self.data, selector), None)

    def test_nonexistent_overridden_default(self):
        selector = 'not-there'
        self.assertEqual(dictpath(self.data, selector, retval=-1), -1)

    def test_no_path(self):
        with self.assertRaises(InvalidPathError):
            dictpath(self.data, None)

    def test_empty_path(self):
        with self.assertRaises(InvalidPathError):
            dictpath(self.data, '...')

    def test_middle_key_not_found(self):
        selector = 'object.oops.type'
        self.assertEqual(dictpath(self.data, selector), None)
