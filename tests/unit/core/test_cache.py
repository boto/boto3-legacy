from boto3.core.cache import ServiceCache
from boto3.core.exceptions import NotCached

from tests import unittest


# Classes for identity tests.
class TestConnection(object): pass
class AnotherTestConnection(TestConnection): pass
class TestResource(object): pass
class AnotherTestResource(TestResource): pass
class TestCollection(object): pass
class AnotherTestCollection(TestCollection): pass


class ServiceCacheTestCase(unittest.TestCase):
    def setUp(self):
        super(ServiceCacheTestCase, self).setUp()
        self.cache = ServiceCache()

    def test_init(self):
        self.assertEqual(self.cache.services, {})

    def test_get_connection(self):
        self.cache.services = {
            'sqs': {
                'connection': TestConnection,
            }
        }

        self.assertEqual(self.cache.get_connection('sqs'), TestConnection)

    def test_get_connection_missing(self):
        self.assertEqual(len(self.cache.services), 0)

        # Unpopulated.
        with self.assertRaises(NotCached):
            self.cache.get_connection('sns')

        # Partially populated.
        self.cache.services['sns'] = {}

        with self.assertRaises(NotCached):
            self.cache.get_connection('sns')

    def test_set_connection(self):
        self.assertEqual(len(self.cache.services), 0)

        self.cache.set_connection('sqs', TestConnection)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'connection': TestConnection,
            },
        })

        # Test a second.
        self.cache.set_connection('sns', AnotherTestConnection)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'connection': TestConnection,
            },
            'sns': {
                'connection': AnotherTestConnection,
            },
        })

    def test_del_connection(self):
        self.cache.services = {
            'sqs': {
                'connection': TestConnection,
            },
            'sns': {
                'connection': AnotherTestConnection,
            },
        }

        self.cache.del_connection('sqs')
        self.assertEqual(self.cache.services, {
            'sqs': {},
            'sns': {
                'connection': AnotherTestConnection,
            },
        })

        # Delete it again. Shouldn't error.
        self.cache.del_connection('sqs')

        # Delete a non-existent service.
        self.cache.del_connection('elastictranscoder')

        self.assertEqual(self.cache.services, {
            'sqs': {},
            'sns': {
                'connection': AnotherTestConnection,
            },
        })

    def test_get_resource(self):
        self.cache.services = {
            'sqs': {
                'resources': {
                    'Test': TestResource,
                }
            }
        }

        self.assertEqual(self.cache.get_resource('sqs', 'Test'), TestResource)

    def test_get_resource_missing(self):
        self.assertEqual(len(self.cache.services), 0)

        # Unpopulated.
        with self.assertRaises(NotCached):
            self.cache.get_resource('sns', 'Test')

        # Partially populated.
        self.cache.services['sns'] = {}

        with self.assertRaises(NotCached):
            self.cache.get_resource('sns', 'Test')

        self.cache.services['sns'] = {
            'resources': {},
        }

        with self.assertRaises(NotCached):
            self.cache.get_resource('sns', 'Test')

    def test_set_resource(self):
        self.assertEqual(len(self.cache.services), 0)

        self.cache.set_resource('sqs', 'Test', TestResource)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'resources': {
                    'Test': TestResource,
                },
            },
        })

        # Test a second.
        self.cache.set_resource('sns', 'AnotherTest', AnotherTestResource)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'resources': {
                    'Test': TestResource,
                },
            },
            'sns': {
                'resources': {
                    'AnotherTest': AnotherTestResource,
                },
            },
        })

    def test_del_resource(self):
        self.cache.services = {
            'sqs': {
                'resources': {
                    'Test': TestResource,
                },
            },
            'sns': {
                'resources': {
                    'AnotherTest': AnotherTestResource,
                },
            },
        }

        self.cache.del_resource('sqs', 'Test')
        self.assertEqual(self.cache.services, {
            'sqs': {
                'resources': {},
            },
            'sns': {
                'resources': {
                    'AnotherTest': AnotherTestResource,
                },
            },
        })

        # Delete it again. Shouldn't error.
        self.cache.del_resource('sqs', 'Test')

        # Delete a non-existent service.
        self.cache.del_resource('elastictranscoder', 'Pipeline')

        self.assertEqual(self.cache.services, {
            'sqs': {
                'resources': {},
            },
            'sns': {
                'resources': {
                    'AnotherTest': AnotherTestResource,
                },
            },
        })

    def test_get_collection(self):
        self.cache.services = {
            'sqs': {
                'collections': {
                    'Test': TestCollection,
                },
            }
        }

        self.assertEqual(
            self.cache.get_collection('sqs', 'Test'),
            TestCollection
        )

    def test_get_collection_missing(self):
        self.assertEqual(len(self.cache.services), 0)

        # Unpopulated.
        with self.assertRaises(NotCached):
            self.cache.get_collection('sns', 'Test')

        # Partially populated.
        self.cache.services['sns'] = {}

        with self.assertRaises(NotCached):
            self.cache.get_collection('sns', 'Test')

    def test_set_collection(self):
        self.assertEqual(len(self.cache.services), 0)

        self.cache.set_collection('sqs', 'Test', TestCollection)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'collections': {
                    'Test': TestCollection,
                },
            },
        })

        # Test a second.
        self.cache.set_collection('sns', 'AnotherTest', AnotherTestCollection)
        self.assertEqual(self.cache.services, {
            'sqs': {
                'collections': {
                    'Test': TestCollection,
                },
            },
            'sns': {
                'collections': {
                    'AnotherTest': AnotherTestCollection,
                },
            },
        })

    def test_del_collection(self):
        self.cache.services = {
            'sqs': {
                'collections': {
                    'Test': TestCollection,
                },
            },
            'sns': {
                'collections': {
                    'AnotherTest': AnotherTestCollection,
                },
            },
        }

        self.cache.del_collection('sqs', 'Test')
        self.assertEqual(self.cache.services, {
            'sqs': {
                'collections': {},
            },
            'sns': {
                'collections': {
                    'AnotherTest': AnotherTestCollection,
                },
            },
        })

        # Delete it again. Shouldn't error.
        self.cache.del_collection('sqs', 'Test')

        # Delete a non-existent service.
        self.cache.del_collection('elastictranscoder', 'Pipeline')

        self.assertEqual(self.cache.services, {
            'sqs': {
                'collections': {},
            },
            'sns': {
                'collections': {
                    'AnotherTest': AnotherTestCollection,
                },
            },
        })

    def test_integration(self):
        self.assertEqual(len(self.cache.services), 0)

        # Do a bunch of semi-complex things & make sure nothing stomps on
        # each other's toes.
        self.cache.set_connection('sqs', AnotherTestConnection)
        self.cache.set_resource('sqs', 'Queue', TestResource)
        self.cache.set_connection('sqs', TestConnection)
        self.cache.set_resource('sqs', 'Message', AnotherTestResource)
        self.cache.del_resource('sqs', 'Message')
        self.cache.set_collection(
            'sqs',
            'QueueCollection',
            AnotherTestCollection
        )
        self.cache.set_resource('sqs', 'Message', TestResource)

        self.cache.set_connection('sns', TestConnection)
        self.cache.set_connection('sns', AnotherTestConnection)
        self.cache.set_connection('sns', TestConnection)

        self.cache.set_collection(
            'elastictranscoder',
            'PipelineCollection',
            AnotherTestCollection
        )

        self.assertEqual(self.cache.services, {
            'sns': {
                'connection': TestConnection,
            },
            'elastictranscoder': {
                'collections': {
                    'PipelineCollection': AnotherTestCollection,
                },
            },
            'sqs': {
                'resources': {
                    'Message': TestResource,
                    'Queue': TestResource,
                },
                'collections': {
                    'QueueCollection': AnotherTestCollection,
                },
                'connection': TestConnection,
            }
        })
