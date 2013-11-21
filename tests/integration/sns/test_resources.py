import time

import boto3
from boto3.sns.utils import subscribe_sqs_queue
from boto3.sqs.utils import convert_queue_url_to_arn
from boto3.utils import json

from tests import unittest


class SNSIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(SNSIntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to('sns', region_name='us-west-2')
        # TODO: We'll use a low-level SQS connection for now, since that will
        #       insulate these tests from failures in the SQS resource layer.
        #       Eventually, we should make sure that the higher-level resources
        #       play together well.
        self.sqs = boto3.session.connect_to('sqs', region_name='us-west-2')

    def test_integration(self):
        TopicCollection = boto3.session.get_collection(
            'sns',
            'TopicCollection'
        )
        Topic = boto3.session.get_resource('sns', 'Topic')
        SubscriptionCollection = boto3.session.get_collection(
            'sns',
            'SubscriptionCollection'
        )
        Subscription = boto3.session.get_resource('sns', 'Subscription')

        topic = TopicCollection(connection=self.conn).create(
            name='my_test_topic'
        )
        self.addCleanup(topic.delete)

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        self.assertTrue(isinstance(topic, Topic))
        self.assertTrue(':my_test_topic' in topic.topic_arn)

        url = self.sqs.create_queue(queue_name='sns_test')['QueueUrl']
        self.addCleanup(self.sqs.delete_queue, queue_url=url)

        # TODO: For now, we'll lean on the utility method.
        #       This should be built into the resource objects, but more thought
        #       is needed on how to manage extension.
        #       Ideally, this looks like something to the effect of:
        #           subscription = SubscriptionCollection().create_with_sqs(
        #               topic=topic_instance,
        #               queue=queue_instance
        #           )
        queue_arn = convert_queue_url_to_arn(self.sqs, url)
        subscribe_sqs_queue(
            self.conn,
            self.sqs,
            topic.get_identifier(),
            url,
            queue_arn
        )

        # Now publish a message to the topic.
        result = topic.publish(
            message=json.dumps({
                'default': 'This is a notification!',
            })
        )

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        # Then check the queue for the message.
        messages = self.sqs.receive_message(
            queue_url=url
        )
        self.assertTrue(len(messages['Messages']) > 0)
        raw_body = messages['Messages'][0]['Body']
        body = json.loads(raw_body)
        msg = json.loads(body.get('Message', '{}'))
        self.assertEqual(msg, {'default': 'This is a notification!'})
