import time

from boto3.core.session import Session

from tests import unittest


class SQSConnectionTestCase(unittest.TestCase):
    def setUp(self):
        super(SQSConnectionTestCase, self).setUp()
        self.sqs_class = Session().get_service('sqs')
        self.sqs = self.sqs_class()

    def test_op_methods(self):
        self.assertTrue(hasattr(self.sqs, 'add_permission'))
        self.assertTrue(callable(self.sqs.add_permission))
        self.assertTrue(hasattr(self.sqs, 'change_message_visibility'))
        self.assertTrue(callable(self.sqs.change_message_visibility))
        self.assertTrue(hasattr(self.sqs, 'change_message_visibility_batch'))
        self.assertTrue(callable(self.sqs.change_message_visibility_batch))
        self.assertTrue(hasattr(self.sqs, 'create_queue'))
        self.assertTrue(callable(self.sqs.create_queue))
        self.assertTrue(hasattr(self.sqs, 'delete_message'))
        self.assertTrue(callable(self.sqs.delete_message))
        self.assertTrue(hasattr(self.sqs, 'delete_message_batch'))
        self.assertTrue(callable(self.sqs.delete_message_batch))
        self.assertTrue(hasattr(self.sqs, 'delete_queue'))
        self.assertTrue(callable(self.sqs.delete_queue))
        self.assertTrue(hasattr(self.sqs, 'get_queue_attributes'))
        self.assertTrue(callable(self.sqs.get_queue_attributes))
        self.assertTrue(hasattr(self.sqs, 'get_queue_url'))
        self.assertTrue(callable(self.sqs.get_queue_url))
        self.assertTrue(hasattr(self.sqs, 'list_queues'))
        self.assertTrue(callable(self.sqs.list_queues))
        self.assertTrue(hasattr(self.sqs, 'receive_message'))
        self.assertTrue(callable(self.sqs.receive_message))
        self.assertTrue(hasattr(self.sqs, 'remove_permission'))
        self.assertTrue(callable(self.sqs.remove_permission))
        self.assertTrue(hasattr(self.sqs, 'send_message'))
        self.assertTrue(callable(self.sqs.send_message))
        self.assertTrue(hasattr(self.sqs, 'send_message_batch'))
        self.assertTrue(callable(self.sqs.send_message_batch))
        self.assertTrue(hasattr(self.sqs, 'set_queue_attributes'))
        self.assertTrue(callable(self.sqs.set_queue_attributes))

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
