import time

import boto3
from boto3.s3.utils import force_delete_bucket

from tests import unittest


class S3IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(S3IntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to('s3', region_name='us-west-2')

    def test_integration(self):
        bucket_name = 'boto3-s3-resources-{0}'.format(int(time.time()))

        BucketCollection = boto3.session.get_collection(
            's3',
            'BucketCollection'
        )
        Bucket = boto3.session.get_resource('s3', 'Bucket')
        S3ObjectCollection = boto3.session.get_collection(
            's3',
            'S3ObjectCollection'
        )
        S3Object = boto3.session.get_resource('s3', 'S3Object')

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

        import pdb; pdb.set_trace()
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

        obj = S3ObjectCollection(connection=self.conn).get(
            # FIXME: This should be passable as an object without having to
            #        pass specific data.
            bucket=bucket_name,
            key='test_key'
        )
        self.assertTrue(isinstance(obj, S3Object))
        self.assertEqual(obj.body, 'THIS IS A TRIUMPH')

        # Test travering relations.
        obj = bucket.keys.get(key='test_key')
        self.assertTrue(isinstance(obj, S3Object))
        self.assertEqual(obj.body, 'THIS IS A TRIUMPH')
