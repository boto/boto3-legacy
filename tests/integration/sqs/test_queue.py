from boto3.session import Session
from boto3.sqs import Queue

from tests import unittest


class QueueTestCase(unittest.TestCase):
    def setUp(self):
        super(QueueTestCase, self).setUp()
        self.session = Session()
        self.queue = Queue(session=self.session)
