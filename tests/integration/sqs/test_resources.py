import time

import boto3

from tests import unittest


class SQSIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSIntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to('sqs', region_name='us-west-2')

    def test_integration(self):
        QueueCollection = boto3.session.get_collection(
            'sqs',
            'QueueCollection'
        )
        Queue = boto3.session.get_resource('sqs', 'Queue')
        MessageCollection = boto3.session.get_collection(
            'sqs',
            'MessageCollection'
        )
        Message = boto3.session.get_resource('sqs', 'Message')

        queue = QueueCollection(connection=self.conn).create(
            queue_name='my_test_queue'
        )
        self.addCleanup(queue.delete)

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        self.assertTrue(isinstance(queue, Queue))
        self.assertTrue('/my_test_queue' in queue.queue_url)

        msg = MessageCollection(
            connection=self.conn,
            # FIXME: This should be passable as an object without having to
            #        pass specific data.
            queue_url=queue.queue_url
        ).create(
            message_body="THIS IS A TRIUMPH"
        )
        self.assertTrue(isinstance(msg, Message))
        self.assertEqual(
            msg.md5_of_message_body,
            '07366f249e11262705e4964e03873078'
        )

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        msgs = MessageCollection(
            connection=self.conn,
            queue_url=queue.queue_url
        ).each()
        self.assertTrue(isinstance(msgs[0], Message))
        self.assertEqual(msgs[0].body, "THIS IS A TRIUMPH")
