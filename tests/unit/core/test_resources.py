import mock
import os

from boto3.core.connection import ConnectionFactory
from boto3.core.constants import DEFAULT_RESOURCE_JSON_DIR
from boto3.core.exceptions import APIVersionMismatchError
from boto3.core.exceptions import NoResourceJSONFound
from boto3.core.resources import ResourceJSONLoader, ResourceDetails
from boto3.core.resources import Resource, ResourceFactory
from boto3.core.session import Session
from boto3.utils import json

from tests import unittest
from tests.unit.fakes import FakeParam, FakeOperation, FakeService, FakeSession


class TestCoreService(FakeService):
    api_version = '2013-08-23'
    operations = [
        FakeOperation(
            'CreateQueue',
            " <p>Creates a queue.</p>\n ",
            params=[
                FakeParam('QueueName', required=True, ptype='string'),
                FakeParam('Attributes', required=False, ptype='map'),
            ],
            output={
                'shape_name': 'CreateQueueResult',
                'type': 'structure',
                'members': {
                    'QueueUrl': {
                        'shape_name': 'String',
                        'type': 'string',
                        'documentation': '\n    <p>The URL for the created SQS queue.</p>\n  ',
                    },
                },
            },
            result=(None, {
                'QueueUrl': 'http://example.com',
            })
        ),
        FakeOperation(
            'SendMessage',
            " <p>Sends a message to a queue.</p>\n ",
            params=[
                FakeParam('QueueName', required=True, ptype='string'),
                FakeParam('MessageBody', required=True, ptype='string'),
                FakeParam('MessageType', required=False, ptype='string'),
            ],
            output=True,
            result=(None, True)
        ),
        FakeOperation(
            'ReceiveMessage',
            " something something something ",
            params=[
                FakeParam('QueueUrl', required=True, ptype='string'),
                FakeParam('AttributeNames', required=False, ptype='list'),
                FakeParam('MaxNumberOfMessages', required=False, ptype='integer'),
                FakeParam('VisibilityTimeout', required=False, ptype='integer'),
                FakeParam('WaitTimeSeconds', required=False, ptype='integer'),
            ],
            output={
                'shape_name': 'ReceiveMessageResult',
                'type': 'structure',
                'members': {
                    'Messages': {
                        'shape_name': 'MessageList',
                        'type': 'list',
                        'members': {
                            'shape_name': 'Message',
                            'type': 'structure',
                            'members': {
                                'MessageId': {
                                    'shape_name': 'String',
                                    'type': 'string',
                                    'documentation': None
                                },
                                'ReceiptHandle': {
                                    'shape_name': 'String',
                                    'type': 'string',
                                    'documentation': None
                                },
                                'MD5OfBody': {
                                    'shape_name': 'String',
                                    'type': 'string',
                                    'documentation': None
                                },
                                'Body': {
                                    'shape_name': 'String',
                                    'type': 'string',
                                    'documentation': None
                                },
                                'Attributes': {
                                    'shape_name': 'AttributeMap',
                                    'type': 'map',
                                    'keys': {
                                        'shape_name': 'QueueAttributeName',
                                        'type': 'string',
                                        'enum': [
                                            'Policy',
                                            'VisibilityTimeout',
                                            'MaximumMessageSize',
                                            'MessageRetentionPeriod',
                                            'ApproximateNumberOfMessages',
                                            'ApproximateNumberOfMessagesNotVisible',
                                            'CreatedTimestamp',
                                            'LastModifiedTimestamp',
                                            'QueueArn',
                                            'ApproximateNumberOfMessagesDelayed',
                                            'DelaySeconds',
                                            'ReceiveMessageWaitTimeSeconds'
                                        ],
                                        'documentation': '\n    <p>The name of a queue attribute.</p>\n  ',
                                        'xmlname': 'Name'
                                    },
                                    'members': {
                                        'shape_name': 'String',
                                        'type': 'string',
                                        'documentation': '\n    <p>The value of a queue attribute.</p>\n  ',
                                        'xmlname': 'Value'
                                    },
                                    'flattened': True,
                                    'xmlname': 'Attribute',
                                    'documentation': None,
                                },
                            },
                            'documentation': None,
                            'xmlname': 'Message'
                        },
                        'flattened': True,
                        'documentation': '\n    <p>A list of messages.</p>\n  '
                    }
                },
                'documentation': None
            },
            result=(None, {
                'Messages': [
                    {
                        'MessageId': 'msg-12345',
                        'ReceiptHandle': 'hndl-12345',
                        'MD5OfBody': '6cd3556deb0da54bca060b4c39479839',
                        'Body': 'Hello, world!',
                        'Attributes': {
                            'QueueArn': 'arn:aws:example:example:sqs:something',
                            'ApproximateNumberOfMessagesDelayed': '2',
                            'DelaySeconds': '10',
                            'CreatedTimestamp': '2013-10-17T21:52:46Z',
                            'LastModifiedTimestamp': '2013-10-17T21:52:46Z',
                        },
                    },
                    {
                        'MessageId': 'msg-12346',
                        'ReceiptHandle': 'hndl-12346',
                        'MD5OfBody': '6cd355',
                        'Body': 'Another message!',
                        'Attributes': {},
                    },
                ]
            })
        ),
        FakeOperation(
            'DeleteQueue',
            " <p>Deletes a queue.</p>\n ",
            params=[
                FakeParam('QueueName', required=True, ptype='string'),
            ],
            output=True,
            result=(None, True)
        ),
    ]


class ResourceJSONLoaderTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceJSONLoaderTestCase, self).setUp()
        self.default_dirs = [
            DEFAULT_RESOURCE_JSON_DIR,
        ]
        self.test_dirs = [
            os.path.join(os.path.dirname(__file__), 'test_data')
        ] + self.default_dirs
        self.default_loader = ResourceJSONLoader(self.default_dirs)
        self.test_loader = ResourceJSONLoader(self.test_dirs)

    def test_init(self):
        self.assertEqual(self.default_loader.data_dirs, self.default_dirs)
        self.assertEqual(self.default_loader._loaded_data, {})
        self.assertEqual(self.test_loader.data_dirs, self.test_dirs)
        self.assertEqual(self.test_loader._loaded_data, {})

    def test_construct_filepath(self):
        self.assertEqual(
            self.test_loader.construct_filepath('/foo/bar', 'baz'),
            '/foo/bar/baz.json'
        )

    def test_load(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        data = self.test_loader.load('test')
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

        # Make sure it didn't get cached here.
        self.assertEqual(len(self.test_loader._loaded_data), 0)

    def test_load_fallback(self):
        # This won't be found in the ``test_data`` directory but is in the
        # main code. Make sure we eventually find it.
        data = self.test_loader.load('elastictranscoder')
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

    def test_getitem(self):
        self.assertEqual(len(self.test_loader._loaded_data), 0)

        # Note the change of calling format here (vs. above).
        data = self.test_loader['test']
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in data)

        # Make sure it **DID** get cached.
        self.assertEqual(len(self.test_loader._loaded_data), 1)
        self.assertTrue('test' in self.test_loader._loaded_data)

    def test_getitem_cached(self):
        # Fake some data into the cache.
        self.test_loader._loaded_data['nonexistent'] = {
            'this is a': 'test',
            'abc': 123,
        }

        # This wouldn't be loadable otherwise (not on the filesystem).
        # However, since we faked it into the cache...
        data = self.test_loader['nonexistent']
        self.assertEqual(data['this is a'], 'test')

    def test_contains(self):
        self.test_loader._loaded_data['foo'] = 'bar'
        self.assertEqual(len(self.test_loader._loaded_data), 1)

        self.assertTrue('foo' in self.test_loader)
        self.assertFalse('nopenopenope' in self.test_loader)

    def test_not_found(self):
        with self.assertRaises(NoResourceJSONFound):
            data = self.test_loader.load('nopenopenope')


class ResourceDetailsTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceDetailsTestCase, self).setUp()
        self.test_dirs = [
            os.path.join(os.path.dirname(__file__), 'test_data')
        ]
        self.test_loader = ResourceJSONLoader(self.test_dirs)
        self.session = Session(FakeSession(TestCoreService()))

        self.rd = ResourceDetails(
            self.session,
            'test',
            'Whatever',
            loader=self.test_loader
        )

    def test_init(self):
        self.assertEqual(self.rd.session, self.session)
        self.assertEqual(self.rd.service_name, 'test')
        self.assertEqual(self.rd.loader, self.test_loader)
        self.assertEqual(self.rd._loaded_data, None)
        self.assertEqual(self.rd._api_versions, None)

    def test_service_data_uncached(self):
        self.assertEqual(self.rd._loaded_data, None)

        data = self.rd.service_data
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_versions' in self.rd._loaded_data)

    def test_api_version_uncached(self):
        self.assertEqual(self.rd._api_versions, None)

        av = self.rd.api_versions
        self.assertEqual(av, [
            '2012-09-25',
        ])
        self.assertEqual(self.rd._api_versions, [
            '2012-09-25',
        ])

    def test_cached(self):
        # Fake in data.
        self.rd._loaded_data = {
            'api_versions': [
                '20XX-MM-II',
            ],
            'hello': 'world',
        }

        data = self.rd.service_data
        av = self.rd.api_versions
        self.assertTrue('hello' in data)
        self.assertTrue('20XX-MM-II' in av)


class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.sf = ResourceFactory(session=self.session)
        self.res_class = self.sf.construct_for('test')
        self.res = self.conn_class()