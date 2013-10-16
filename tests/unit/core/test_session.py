from botocore.service import Service as BotocoreService

from boto3.core.session import Session

from tests import unittest


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()
        Session._reset()
        self.session = Session()

    def test_get_core_service(self):
        client = self.session.get_core_service('sqs')
        self.assertTrue(isinstance(client, BotocoreService))

    def test_get_service_exists(self):
        self.assertEqual(len(Session.conn_classes), 0)
        # Put in a sentinel.
        Session.conn_classes['test'] = None
        self.assertEqual(len(Session.conn_classes), 1)

        client = self.session.get_service('test')
        self.assertTrue(client is None)

    def test_get_service_does_not_exist(self):
        self.assertEqual(len(self.session.conn_classes), 0)
        client = self.session.get_service('sqs')
        self.assertEqual(client.__name__, 'SqsConnection')
        self.assertEqual(len(self.session.conn_classes), 1)

    def test_connect_to_region(self):
        client = self.session.connect_to('sqs', region_name='us-west-2')
        self.assertEqual(client.__class__.__name__, 'SqsConnection')
        self.assertEqual(client.region_name, 'us-west-2')


if __name__ == "__main__":
    unittest.main()
