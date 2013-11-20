import boto3
from boto3.sqs.utils import convert_queue_url_to_arn

from tests import unittest


class SQSUtilsTestCase(unittest.TestCase):
    def test_convert_queue_url_to_arn(self):
        sqs = boto3.session.connect_to('sqs')
        url = 'https://queue.amazonaws.com/099270012/test_test_test'
        self.assertEqual(
            convert_queue_url_to_arn(sqs, url),
            'arn:aws:sqs:us-east-1:099270012:test_test_test'
        )
