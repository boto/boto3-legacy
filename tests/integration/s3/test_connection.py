# -*- coding: utf-8 -*-
import time

from boto3.core.session import Session
from boto3.s3.utils import force_delete_bucket
from boto3.utils import six

from tests import unittest


class S3ConnectionTestCase(unittest.TestCase):
    def setUp(self):
        super(S3ConnectionTestCase, self).setUp()
        self.s3_class = Session().get_connection('s3')
        self.s3 = self.s3_class()

    def test_op_methods(self):
        ops = [
            'abort_multipart_upload',
            'complete_multipart_upload',
            'copy_object',
            'create_bucket',
            'create_multipart_upload',
            'delete_bucket',
            'delete_bucket_cors',
            'delete_bucket_lifecycle',
            'delete_bucket_policy',
            'delete_bucket_tagging',
            'delete_bucket_website',
            'delete_object',
            'delete_objects',
            'get_bucket_acl',
            'get_bucket_cors',
            'get_bucket_lifecycle',
            'get_bucket_location',
            'get_bucket_logging',
            'get_bucket_notification',
            'get_bucket_policy',
            'get_bucket_request_payment',
            'get_bucket_tagging',
            'get_bucket_versioning',
            'get_bucket_website',
            'get_object',
            'get_object_acl',
            'get_object_torrent',
            'head_bucket',
            'head_object',
            'list_buckets',
            'list_multipart_uploads',
            'list_object_versions',
            'list_objects',
            'list_parts',
            'put_bucket_acl',
            'put_bucket_cors',
            'put_bucket_lifecycle',
            'put_bucket_logging',
            'put_bucket_notification',
            'put_bucket_policy',
            'put_bucket_request_payment',
            'put_bucket_tagging',
            'put_bucket_versioning',
            'put_bucket_website',
            'put_object',
            'put_object_acl',
            'restore_object',
            'upload_part',
            'upload_part_copy'
        ]

        for op_name in ops:
            self.assertTrue(
                hasattr(self.s3, op_name),
                msg="{0} is missing.".format(op_name)
            )
            self.assertTrue(
                callable(getattr(self.s3, op_name)),
                msg="{0} is not callable.".format(op_name)
            )

    def test_integration(self):
        bucket_name = 'boto3_test_s3_{0}'.format(time.time())
        key_name = 'hello.txt'

        resp = self.s3.create_bucket(
            bucket=bucket_name
        )

        self.addCleanup(
            force_delete_bucket,
            conn=self.s3,
            bucket_name=bucket_name
        )

        # FIXME: Needs 100% more waiters.
        time.sleep(5)

        buckets = [buck['Name'] for buck in self.s3.list_buckets()['Buckets']]
        self.assertTrue(bucket_name in buckets)

        self.s3.put_object(
            bucket=bucket_name,
            key=key_name,
            body='Some test data'
            # FIXME: This fails miserably with Unicode. Neither of the following
            #        work. Figure out what the right solution is.
            # body=u'Some test data about ☃'
            # body=u'Some test data about ☃'.encode('utf-8')
        )
        time.sleep(5)

        s3_object = self.s3.get_object(
            bucket=bucket_name,
            key=key_name
        )
        body = s3_object['Body'].read()
        self.assertEqual(body, b'Some test data')
        # body = s3_object['Body'].read().decode('utf-8')
        # self.assertEqual(body, u'Some test data about ☃')
