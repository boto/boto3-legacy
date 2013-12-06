import time

import boto3
from boto3.elastictranscoder.resources import PipelineCollection
from boto3.elastictranscoder.resources import Pipeline
from boto3.iam.constants import ASSUME_ROLE_POLICY_DOCUMENT
from boto3.iam.resources import RoleCollection
from boto3.s3.resources import BucketCollection
from boto3.s3.utils import force_delete_bucket

from tests import unittest


class ElasticTranscoderIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(ElasticTranscoderIntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to(
            'elastictranscoder',
            region_name='us-west-2'
        )

    def test_integration(self):
        iam_conn = boto3.session.connect_to('iam')
        s3_conn = boto3.session.connect_to('s3')

        now = int(time.time())
        role_name = 'test-pipeline-{0}'.format(now)
        in_bucket = 'test-pipeline-in-{0}'.format(now)
        out_bucket = 'test-pipeline-out-{0}'.format(now)
        pipeline_name = 'pipeline-{0}'.format(now)

        # Do the requisite setup.
        role = RoleCollection(connection=iam_conn).create(
            role_name=role_name,
            assume_role_policy_document=ASSUME_ROLE_POLICY_DOCUMENT
        )
        # FIXME: This shouldn't be necessary...
        self.addCleanup(role.delete, role_name=role_name)

        resp = BucketCollection(connection=s3_conn).create(bucket=in_bucket)
        self.addCleanup(
            force_delete_bucket,
            conn=s3_conn,
            bucket_name=in_bucket
        )
        resp = BucketCollection(connection=s3_conn).create(bucket=out_bucket)
        self.addCleanup(
            force_delete_bucket,
            conn=s3_conn,
            bucket_name=out_bucket
        )

        # Now list/create/list/read/update the pipeline.
        pipelines = PipelineCollection().each()
        pipeline_names = [pipe.name for pipe in pipelines]
        self.assertFalse(pipeline_name in pipeline_names)

        pipe = PipelineCollection().create(
            name=pipeline_name,
            input_bucket=in_bucket,
            output_bucket=out_bucket,
            role=role.arn,
            notifications={
                'Completed': '',
                'Error': '',
                'Warning': '',
                'Progressing': '',
            }
        )
        pipeline_id = pipe.id

        pipelines = PipelineCollection().each()
        pipeline_names = [pipe.name for pipe in pipelines]
        self.assertTrue(pipeline_name in pipeline_names)

        pipeline = Pipeline(id=pipeline_id)
        pipeline.get()
        self.assertEqual(pipeline.name, pipeline_name)

        resp = pipeline.update_status(status='Paused')
        self.assertEqual(resp['Pipeline']['Status'], 'Paused')
