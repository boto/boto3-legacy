from botocore.service import Service as BotocoreService

from boto3.core.session import Session

from tests import unittest


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()
        self.session = Session()

    def test_get_service(self):
        client = self.session.get_service('sqs')
        self.assertTrue(isinstance(client, BotocoreService))


if __name__ == "__main__":
    unittest.main()
