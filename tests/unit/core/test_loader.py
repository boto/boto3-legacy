import os

from boto3.core.constants import DEFAULT_RESOURCE_JSON_DIR
from boto3.core.exceptions import NoResourceJSONFound
from boto3.core.loader import ResourceJSONLoader

from tests import unittest


class ResourceJSONLoaderTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceJSONLoaderTestCase, self).setUp()
        self.default_dirs = [
            DEFAULT_RESOURCE_JSON_DIR,
        ]
        self.test_dirs = [
            os.path.join(os.path.dirname(__file__), 'test_data')
        ] + self.default_dirs
        self.default_loader = ResourceJSONLoader(self.default_dirs)
        self.test_loader = ResourceJSONLoader(self.test_dirs)

    def test_init(self):
        self.assertEqual(self.default_loader.data_dirs, self.default_dirs)
        self.assertEqual(self.default_loader._loaded_data, {})
        self.assertEqual(self.test_loader.data_dirs, self.test_dirs)
        self.assertEqual(self.test_loader._loaded_data, {})

    def test_construct_filepath(self):
        self.assertEqual(
            self.test_loader.construct_filepath('/foo/bar', 'baz'),
            '/foo/bar/baz.json'
        )

    def test_load(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        data = self.test_loader.load('test')
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

        # Make sure it didn't get cached here.
        self.assertEqual(len(self.test_loader._loaded_data), 0)

    def test_load_fallback(self):
        # This won't be found in the ``test_data`` directory but is in the
        # main code. Make sure we eventually find it.
        data = self.test_loader.load('elastictranscoder')
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

    def test_getitem(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        # Note the change of calling format here (vs. above).
        data = self.test_loader['test']
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

        # Make sure it **DID** get cached.
        self.assertEqual(len(self.test_loader._loaded_data), 1)
        self.assertTrue('test' in self.test_loader._loaded_data)

    def test_getitem_cached(self):
        # Fake some data into the cache.
        self.test_loader._loaded_data['nonexistent'] = {
            'this is a': 'test',
            'abc': 123,
        }

        # This wouldn't be loadable otherwise (not on the filesystem).
        # However, since we faked it into the cache...
        data = self.test_loader['nonexistent']
        self.assertEqual(data['this is a'], 'test')

    def test_contains(self):
        self.test_loader._loaded_data['foo'] = 'bar'
        self.assertEqual(len(self.test_loader._loaded_data), 1)

        self.assertTrue('foo' in self.test_loader)
        self.assertFalse('nopenopenope' in self.test_loader)

    def test_not_found(self):
        with self.assertRaises(NoResourceJSONFound):
            self.test_loader.load('nopenopenope')
