import os
import shutil

from botocore.service import Service as BotocoreService

from boto3.constants import AWS_JSON_PATHS
from boto3.exceptions import ServiceNotFound
from boto3.session import Session

from tests import unittest


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        super(SessionTestCase, self).setUp()
        self.session = Session()
        self.tmp_path = os.path.join('/tmp', 'boto3_session_test')
        self.overrides_paths = [self.tmp_path] + AWS_JSON_PATHS

        shutil.rmtree(self.tmp_path, ignore_errors=True)
        os.makedirs(self.tmp_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_path, ignore_errors=True)
        super(SessionTestCase, self).tearDown()

    def test_load_json_for_sqs(self):
        sqs_json = self.session.load_json_for('sqs')
        self.assertEqual(sqs_json['objects'], [
            'Queue',
            'Message',
        ])

    def test_load_json_for_nonexistent_service(self):
        self.assertRaises(
            ServiceNotFound, self.session.load_json_for, 'whatever'
        )

    def test_load_json_for_nonexistent_path(self):
        session = Session(json_paths=[self.tmp_path])
        # This file shouldn't exist at any location, so it's not loadable.
        self.assertRaises(
            ServiceNotFound, session.load_json_for, 'whatever'
        )

    def test_load_json_for_custom_path(self):
        with open(os.path.join(self.tmp_path, 'sqs.json'), 'w') as json_file:
            json_file.write('{"objects": ["MyQueue"]}')

        session = Session(json_paths=self.overrides_paths)
        # This should load the overridden JSON.
        sqs_json = session.load_json_for('sqs')
        self.assertEqual(sqs_json['objects'], [
            'MyQueue',
        ])

    def test_load_json_for_multiple_paths(self):
        json_filename = os.path.join(self.tmp_path, 'whatever.json')

        with open(json_filename, 'w') as json_file:
            json_file.write('{"objects": ["AnObject"]}')

        session = Session(json_paths=self.overrides_paths)
        # This should appropriately fall through to the base directory.
        sqs_json = session.load_json_for('sqs')
        self.assertEqual(sqs_json['objects'], [
            'Queue',
            'Message',
        ])

    def test_get_client(self):
        client = self.session.get_client('sqs')
        self.assertTrue(isinstance(client, BotocoreService))


if __name__ == "__main__":
    unittest.main()
