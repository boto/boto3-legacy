from boto3 import session
from boto3.sqs.resources import SQSQueue
from boto3.sqs.resources import SQSQueueCollection
from boto3.sqs.resources import SQSMessage

from tests import unittest


class SQSQueueTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSQueueTestCase, self).setUp()
        SQSConnection = session.get_service('sqs')
        self.conn = SQSConnection(region_name='us-west-2')

    def test_integration(self):
        # Do we default to the main session (dangerous)?
        #     queue = SQSQueue.collection.create('my_test_queue')
        # ...or do you have to manually instantiate?
        queue = SQSQueueCollection(connection=self.conn).create('my_test_queue')
        self.addCleanup(queue.delete)

        self.assertTrue(isinstance(queue, SQSQueue))
        self.assertEqual(queue.name, 'my_test_queue')
        self.assertTrue('/my_test_queue' in queue.url)

        queue.send_message(
            message_body="THIS IS A TRIUMPH"
        )

        msg = queue.receive_message()
        self.assertTrue(isinstance(msg, SQSMessage))
        self.assertEqual(msg.body, "THIS IS A TRIUMPH")
