from botocore.service import Service as BotocoreService

from boto3.core.session import Session

from tests import unittest


class FakeConnection(object): pass


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()
        self.session = Session()

    def test_get_core_service(self):
        client = self.session.get_core_service('sqs')
        self.assertTrue(isinstance(client, BotocoreService))

    def test_get_connection_exists(self):
        self.assertEqual(len(self.session.cache), 0)
        # Put in a sentinel.
        self.session.cache.set_connection('test', FakeConnection)
        self.assertEqual(len(self.session.cache), 1)

        client = self.session.get_connection('test')
        self.assertTrue(client is FakeConnection)

    def test_get_connection_does_not_exist(self):
        self.assertEqual(len(self.session.cache), 0)
        client = self.session.get_connection('sqs')
        self.assertEqual(client.__name__, 'SqsConnection')
        self.assertEqual(len(self.session.cache), 1)

    def test_get_resource_exists(self):
        self.assertEqual(len(self.session.cache), 0)
        # Put in a sentinel.
        self.session.cache.set_resource('test', 'Test', FakeConnection)
        self.assertEqual(len(self.session.cache), 1)

        Test = self.session.get_resource('test', 'Test')
        self.assertTrue(Test is FakeConnection)

    def test_get_resource_does_not_exist(self):
        self.assertEqual(len(self.session.cache), 0)
        Queue = self.session.get_resource('sqs', 'Queue')
        self.assertEqual(Queue.__name__, 'Queue')
        self.assertEqual(len(self.session.cache), 1)

    def test_get_collection_exists(self):
        self.assertEqual(len(self.session.cache), 0)
        # Put in a sentinel.
        self.session.cache.set_collection('test', 'Test', FakeConnection)
        self.assertEqual(len(self.session.cache), 1)

        TestCollection = self.session.get_collection('test', 'Test')
        self.assertTrue(TestCollection is FakeConnection)

    def test_get_collection_does_not_exist(self):
        self.assertEqual(len(self.session.cache), 0)
        QueueCollection = self.session.get_collection('sqs', 'QueueCollection')
        self.assertEqual(QueueCollection.__name__, 'QueueCollection')
        self.assertEqual(len(self.session.cache), 1)

    def test_connect_to_region(self):
        client = self.session.connect_to('sqs', region_name='us-west-2')
        self.assertEqual(client.__class__.__name__, 'SqsConnection')
        self.assertEqual(client.region_name, 'us-west-2')


if __name__ == "__main__":
    unittest.main()
