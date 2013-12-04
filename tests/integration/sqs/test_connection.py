import time

from tests.integration.base import ConnectionTestCase
from tests import unittest


class SQSConnectionTestCase(ConnectionTestCase, unittest.TestCase):
    service_name = 'sqs'
    ops = [
        'add_permission',
        'change_message_visibility',
        'change_message_visibility_batch',
        'create_queue',
        'delete_message',
        'delete_message_batch',
        'delete_queue',
        'get_queue_attributes',
        'get_queue_url',
        'list_queues',
        'receive_message',
        'remove_permission',
        'send_message',
        'send_message_batch',
        'set_queue_attributes',
    ]

    def test_integration(self):
        name = 'boto3_lives'
        url = self.conn.create_queue(
            queue_name=name
        )['QueueUrl']

        self.addCleanup(self.conn.delete_queue, queue_url=url)

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        urls = self.conn.list_queues()['QueueUrls']
        self.assertTrue(url in urls)

        self.conn.send_message(
            queue_url=url,
            message_body='Does it work?'
        )
        time.sleep(5)

        messages = self.conn.receive_message(
            queue_url=url
        )
        self.assertEqual(messages['Messages'][0]['Body'], 'Does it work?')
