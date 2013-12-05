# -*- coding: utf-8 -*-
import time

import boto3
from boto3.s3.utils import force_delete_bucket
from boto3.sns.utils import subscribe_sqs_queue
from boto3.sqs.utils import convert_queue_url_to_arn
from boto3.utils import json

from tests.integration.base import ConnectionTestCase
from tests import unittest


class ElastictranscoderConnectionTestCase(ConnectionTestCase, unittest.TestCase):
    service_name = 'elastictranscoder'
    ops = [
        'cancel_job',
        'create_job',
        'create_pipeline',
        'create_preset',
        'delete_pipeline',
        'delete_preset',
        'list_jobs_by_pipeline',
        'list_jobs_by_status',
        'list_pipelines',
        'list_presets',
        'read_job',
        'read_pipeline',
        'read_preset',
        'test_role',
        'update_pipeline',
        'update_pipeline_notifications',
        'update_pipeline_status'
    ]
    # FIXME: From Boto v2. Perhaps this should move/be assumed elsewhere?
    ASSUME_ROLE_POLICY_DOCUMENT = json.dumps({
        'Statement': [
            {
                'Principal': {
                    'Service': ['ec2.amazonaws.com']
                },
                'Effect': 'Allow',
                'Action': ['sts:AssumeRole']
            }
        ]
    })

    def test_integration(self):
        iam_conn = boto3.session.connect_to('iam')
        s3_conn = boto3.session.connect_to('s3')

        now = int(time.time())
        role_name = 'test-pipeline-{0}'.format(now)
        in_bucket = 'test-pipeline-in-{0}'.format(now)
        out_bucket = 'test-pipeline-out-{0}'.format(now)
        pipeline_name = 'pipeline-{0}'.format(now)

        # Create the surrounding setup.
        resp = iam_conn.create_role(
            role_name=role_name,
            assume_role_policy_document=self.ASSUME_ROLE_POLICY_DOCUMENT
        )
        self.addCleanup(iam_conn.delete_role, role_name=role_name)
        role_arn = resp['Role']['Arn']

        s3_conn.create_bucket(bucket=in_bucket)
        self.addCleanup(
            force_delete_bucket,
            conn=s3_conn,
            bucket_name=in_bucket
        )
        s3_conn.create_bucket(bucket=out_bucket)
        self.addCleanup(
            force_delete_bucket,
            conn=s3_conn,
            bucket_name=out_bucket
        )

        # Test the pipeline related methods.
        resp = self.conn.list_pipelines()
        initial_pipelines = [pipe['Name'] for pipe in resp['Pipelines']]
        self.assertTrue(not pipeline_name in initial_pipelines)

        # Create a pipeline.
        resp = self.conn.create_pipeline(
            name=pipeline_name,
            input_bucket=in_bucket,
            output_bucket=out_bucket,
            role=role_arn,
            notifications={
                'Completed': '',
                'Error': '',
                'Warning': '',
                'Progressing': '',
            }
        )
        pipeline_id = resp['Pipeline']['Id']
        self.addCleanup(self.conn.delete_pipeline, id=pipeline_id)

        # Ensure it appears in the list.
        resp = self.conn.list_pipelines()
        pipelines = [pipe['Name'] for pipe in resp['Pipelines']]
        self.assertTrue(len(pipelines) > len(initial_pipelines))
        self.assertTrue(pipeline_name in pipelines)

        # Read the pipeline.
        resp = self.conn.read_pipeline(id=pipeline_id)
        self.assertEqual(resp['Pipeline']['Name'], pipeline_name)

        # Update the pipeline.
        resp = self.conn.update_pipeline_status(
            id=pipeline_id,
            status='Paused'
        )
        self.assertEqual(resp['Pipeline']['Status'], 'Paused')
