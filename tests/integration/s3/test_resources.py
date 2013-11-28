import time

import boto3
from boto3.s3.resources import BucketCollection, S3ObjectCollection
from boto3.s3.resources import Bucket, S3Object
from boto3.s3.utils import force_delete_bucket

from tests import unittest


class S3IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(S3IntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to('s3', region_name='us-west-2')

    def test_integration(self):
        bucket_name = 'boto3-s3-resources-{0}'.format(int(time.time()))

        bucket = BucketCollection(connection=self.conn).create(
            bucket=bucket_name,
            create_bucket_configuration={
                'LocationConstraint': 'us-west-2'
            }
        )
        self.addCleanup(
            force_delete_bucket,
            conn=self.conn,
            bucket_name=bucket_name
        )

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        self.assertTrue(isinstance(bucket, Bucket))
        self.assertTrue(bucket_name in bucket.location)

        obj = S3ObjectCollection(connection=self.conn).create(
            # FIXME: This should be passable as an object without having to
            #        pass specific data.
            bucket=bucket_name,
            key='test_key',
            body="THIS IS A TRIUMPH"
        )
        self.assertTrue(isinstance(obj, S3Object))

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        obj = S3Object(
            connection=self.conn,
            # FIXME: This should be passable as an object without having to
            #        pass specific data.
            bucket=bucket_name,
            key='test_key'
        )
        # Update from the service.
        resp = obj.get()

        self.assertTrue(isinstance(obj, S3Object))
        # FIXME: We get a bytestring back rather than a Unicode string.
        #        Is this intended behavior?
        self.assertEqual(obj.get_content(), b'THIS IS A TRIUMPH')
        # self.assertEqual(obj.get_content(), 'THIS IS A TRIUMPH')

        # Test travering relations.
        obj = bucket.objects.get(key='test_key')
        self.assertTrue(isinstance(obj, S3Object))
        self.assertEqual(obj.body, 'THIS IS A TRIUMPH')
