import time

from boto3.core.session import Session

from tests import unittest


class SQSConnectionTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSConnectionTestCase, self).setUp()
        self.sqs_class = Session().get_connection('sqs')
        self.sqs = self.sqs_class()

    def test_op_methods(self):
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

        for op_name in ops:
            self.assertTrue(
                hasattr(self.sqs, op_name),
                msg="{0} is missing.".format(op_name)
            )
            self.assertTrue(
                callable(getattr(self.sqs, op_name)),
                msg="{0} is not callable.".format(op_name)
            )

    def test_integration(self):
        name = 'boto3_lives'
        url = self.sqs.create_queue(
            queue_name=name
        )['QueueUrl']

        self.addCleanup(self.sqs.delete_queue, queue_url=url)

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        urls = self.sqs.list_queues()['QueueUrls']
        self.assertTrue(url in urls)

        self.sqs.send_message(
            queue_url=url,
            message_body='Does it work?'
        )
        time.sleep(5)

        messages = self.sqs.receive_message(
            queue_url=url
        )
        self.assertEqual(messages['Messages'][0]['Body'], 'Does it work?')
