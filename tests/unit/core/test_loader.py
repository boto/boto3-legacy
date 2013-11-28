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

    def test_get_available_options(self):
        opts = self.test_loader.get_available_options('test')
        self.assertTrue('2013-11-27' in opts)
        self.assertTrue(
            'test_data/test-2013-11-27.json' in opts['2013-11-27'][0]
        )

        opts = self.test_loader.get_available_options('s3')
        self.assertTrue('2006-03-01' in opts)
        self.assertTrue(
            'data/aws/resources/s3-2006-03-01.json' in opts['2006-03-01'][0]
        )

    def test_get_best_match(self):
        options = {
            '2013-11-27': [
                '~/.boto-overrides/s3-2013-11-27.json',
                '/path/to/boto3/data/aws/resources/s3-2013-11-27.json',
            ],
            '2010-10-06': [
                '/path/to/boto3/data/aws/resources/s3-2010-10-06.json',
            ],
            '2007-09-15': [
                '~/.boto-overrides/s3-2007-09-15.json',
            ],
        }

        # Latest.
        self.assertEqual(
            self.test_loader.get_best_match(options, 'test'),
            ('~/.boto-overrides/s3-2013-11-27.json', '2013-11-27')
        )
        # Exact match.
        self.assertEqual(
            self.test_loader.get_best_match(
                options,
                'test',
                api_version='2010-10-06'
            ),
            (
                '/path/to/boto3/data/aws/resources/s3-2010-10-06.json',
                '2010-10-06'
            )
        )
        # Best compatible.
        self.assertEqual(
            self.test_loader.get_best_match(
                options,
                'test',
                api_version='2008-02-02'
            ),
            ('~/.boto-overrides/s3-2007-09-15.json', '2007-09-15')
        )

        # No match.
        with self.assertRaises(NoResourceJSONFound):
            self.test_loader.get_best_match(
                options,
                'test',
                api_version='2001-01-01'
            )

    def test_load(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        data = self.test_loader.load('test', cached=False)
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_version' in data)

        # Make sure it didn't get cached here.
        self.assertEqual(len(self.test_loader._loaded_data), 0)

    def test_load_fallback(self):
        # This won't be found in the ``test_data`` directory but is in the
        # main code. Make sure we eventually find it.
        data = self.test_loader.load('elastictranscoder', cached=False)
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_version' in data)

    def test_load_caching(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        # Note the change of calling format here (vs. above).
        data = self.test_loader.load('test')
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_version' in data)

        # Make sure it **DID** get cached.
        self.assertEqual(len(self.test_loader._loaded_data), 1)
        self.assertTrue('test' in self.test_loader._loaded_data)

    def test_load_cached(self):
        # Fake some data into the cache.
        self.test_loader._loaded_data['nonexistent'] = {
            'test': {
                'this is a': 'test',
                'abc': 123,
            },
        }

        # This wouldn't be loadable otherwise (not on the filesystem).
        # However, since we faked it into the cache...
        data = self.test_loader.load('nonexistent', api_version='test')
        self.assertEqual(data['this is a'], 'test')

    def test_contains(self):
        self.test_loader._loaded_data['foo'] = 'bar'
        self.assertEqual(len(self.test_loader._loaded_data), 1)

        self.assertTrue('foo' in self.test_loader)
        self.assertFalse('nopenopenope' in self.test_loader)

    def test_not_found(self):
        with self.assertRaises(NoResourceJSONFound):
            self.test_loader.load('nopenopenope')
