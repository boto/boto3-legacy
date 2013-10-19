import datetime

from boto3.utils.dictpath import DictPath, InvalidPathError

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
        self.path = DictPath(self.data)

    def test_find_simple_data(self):
        selector = 'object.id'
        self.assertEqual(self.path.find(selector), 7)

    def test_find_list_data(self):
        selector = 'object.owner_ids'
        self.assertEqual(self.path.find(selector), [3, 25])

    def test_find_single_key(self):
        selector = 'request_id'
        self.assertEqual(self.path.find(selector), 'abc123')

    def test_find_single_key_complex_data(self):
        selector = 'meta'
        self.assertEqual(self.path.find(selector), {
            'next': '/?page=3',
            'prev': '/?page=1',
            'count': 64,
        })

    def test_find_deeper_fetch(self):
        selector = 'object.properties.type'
        self.assertEqual(self.path.find(selector), 'document')

    def test_find_nonexistent(self):
        selector = 'not-there'
        self.assertEqual(self.path.find(selector), None)

    def test_find_nonexistent_overridden_default(self):
        selector = 'not-there'
        self.assertEqual(self.path.find(selector, retval=-1), -1)

    def test_find_no_path(self):
        with self.assertRaises(InvalidPathError):
            self.path.find(None)

    def test_find_empty_path(self):
        with self.assertRaises(InvalidPathError):
            self.path.find('...')

    def test_find_middle_key_not_found(self):
        selector = 'object.oops.type'
        self.assertEqual(self.path.find(selector), None)

    def test_store_single_key(self):
        self.assertFalse('test' in self.data)

        selector = 'test'
        self.path.store(selector, 'This is a triumph!')
        self.assertTrue('test' in self.data)

    def test_store_deeper(self):
        self.assertFalse('last_edited' in self.data['object']['properties'])

        selector = 'object.properties.last_edited'
        self.path.store(selector, 'daniel')
        self.assertTrue('last_edited' in self.data['object']['properties'])

    def test_store_missing_intermediate(self):
        self.assertFalse('test' in self.data)

        selector = 'test.to_be_created.it_happened'
        self.path.store(selector, 'Yup')
        self.assertEqual(self.data['test'], {
            'to_be_created': {
                'it_happened': 'Yup'
            }
        })

    def test_store_no_path(self):
        with self.assertRaises(InvalidPathError):
            self.path.store(None, 'not happening')

    def test_store_empty_path(self):
        with self.assertRaises(InvalidPathError):
            self.path.store('...', 'not happening')
