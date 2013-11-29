import mock
import os

from boto3.core.connection import ConnectionFactory
from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.exceptions import APIVersionMismatchError
from boto3.core.collections import ResourceJSONLoader, CollectionDetails
from boto3.core.collections import Collection, CollectionFactory
from boto3.core.resources import Resource, ResourceDetails
from boto3.core.session import Session

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


class CollectionDetailsTestCase(unittest.TestCase):
    def setUp(self):
        super(CollectionDetailsTestCase, self).setUp()
        self.test_dirs = [
            os.path.join(os.path.dirname(__file__), 'test_data')
        ]
        self.test_loader = ResourceJSONLoader(self.test_dirs)
        self.session = Session(FakeSession(TestCoreService()))

        self.cd = CollectionDetails(
            self.session,
            'test',
            'PipelineCollection',
            loader=self.test_loader
        )

        # Fake some identifiers in.
        self.alt_cd = CollectionDetails(
            self.session,
            'test',
            'JobCollection',
            loader=self.test_loader
        )
        self.alt_cd._loaded_data = {
            'api_version': 'something',
            'collections': {
                'JobCollection': {
                    'resource': 'Job',
                    'identifiers': [
                        {
                            'var_name': 'pipeline',
                            'api_name': '$whatever.Pipeline',
                        },
                        {
                            'var_name': 'id',
                            'api_name': 'Id',
                        },
                    ],
                    'operations': {}
                }
            }
        }

    def test_init(self):
        self.assertEqual(self.cd.session, self.session)
        self.assertEqual(self.cd.service_name, 'test')
        self.assertEqual(self.cd.loader, self.test_loader)
        self.assertEqual(self.cd._loaded_data, None)
        self.assertEqual(self.cd._api_version, None)

    def test_service_data_uncached(self):
        self.assertEqual(self.cd._loaded_data, None)

        data = self.cd.service_data
        self.assertEqual(len(data.keys()), 4)
        self.assertTrue('api_version' in self.cd._loaded_data)

    def test_collection_data_uncached(self):
        self.assertEqual(self.cd._loaded_data, None)

        data = self.cd.collection_data
        self.assertEqual(len(data.keys()), 2)
        self.assertFalse('identifier' in data)
        self.assertTrue('operations' in data)
        self.assertTrue('api_version' in self.cd._loaded_data)

    def test_api_version_uncached(self):
        self.assertEqual(self.cd._api_version, None)

        av = self.cd.api_version
        self.assertEqual(av, '2013-11-27')
        self.assertEqual(self.cd._api_version, '2013-11-27')

    def test_identifiers(self):
        self.assertEqual(self.cd.identifiers, [])

        # Now with something with identifiers.
        self.assertEqual(self.alt_cd.identifiers, [
            {
                'api_name': '$whatever.Pipeline',
                'var_name': 'pipeline',
            },
            {
                'api_name': 'Id',
                'var_name': 'id',
            }
        ])

    def test_resource_uncached(self):
        self.assertEqual(self.cd._loaded_data, None)

        res = self.cd.resource
        self.assertEqual(res, 'Pipeline')
        self.assertTrue('api_version' in self.cd._loaded_data)

    def test_cached(self):
        # Fake in data.
        self.cd._loaded_data = {
            'api_version': '20XX-MM-II',
            'hello': 'world',
        }

        data = self.cd.service_data
        av = self.cd.api_version
        self.assertTrue('hello' in data)
        self.assertTrue('20XX-MM-II' in av)


class FakeConn(object):
    def __init__(self, *args, **kwargs):
        super(FakeConn, self).__init__()

    def create_pipeline(self, *args, **kwargs):
        return {
            'RequestId': '1234-1234-1234-1234',
            'Id': '1872baf45',
            'Title': 'A pipe',
        }


class FakePipeResource(object):
    def __init__(self, **kwargs):
        # Yuck yuck yuck. Fake fake fake.
        self.__dict__.update(kwargs)


class PipeCollection(Collection):
    def create(self, *args, **kwargs):
        return {}

    def update_params(self, conn_method_name, params):
        params['global'] = True
        return super(PipeCollection, self).update_params(conn_method_name, params)

    def update_params_create(self, params):
        params['created'] = True
        return params

    def post_process(self, conn_method_name, result):
        self.identifier = result.pop('Id')
        return result

    def post_process_create(self, result):
        self.created = True
        return result


class JobCollection(Collection):
    pass


class CollectionTestCase(unittest.TestCase):
    def setUp(self):
        super(CollectionTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.fake_details = CollectionDetails(
            self.session,
            'test',
            'PipeCollection'
        )
        self.fake_alt_details = CollectionDetails(
            self.session,
            'test',
            'JobCollection'
        )
        self.fake_details._loaded_data = {
            'api_version': 'something',
            'collections': {
                'PipeCollection': {
                    'resource': 'Pipeline',
                    'operations': {
                        'create': {
                            'api_name': 'CreatePipe'
                        }
                    }
                },
                'JobCollection': {
                    'resource': 'Job',
                    'identifiers': [
                        {
                            'var_name': 'pipeline',
                            'api_name': '$whatever.Pipeline',
                        },
                        {
                            'var_name': 'id',
                            'api_name': 'Id',
                        },
                    ],
                    'operations': {}
                }
            }
        }
        self.fake_alt_details._loaded_data = self.fake_details._loaded_data
        self.fake_conn = FakeConn()

        PipeCollection._details = self.fake_details
        self.collection = PipeCollection(
            connection=self.fake_conn,
            id='1872baf45'
        )
        JobCollection._details = self.fake_alt_details
        self.alt_collection = JobCollection(
            connection=self.fake_conn,
            pipeline='fake-pipe',
            id='8716fc26a'
        )

    def test_get_identifiers(self):
        # No identifiers.
        self.assertEqual(self.collection.get_identifiers(), {})

        # Has identifiers.
        self.assertEqual(self.alt_collection.get_identifiers(), {
            'id': '8716fc26a',
            'pipeline': 'fake-pipe',
        })

    def test_set_identifiers(self):
        self.assertEqual(self.alt_collection._data, {
            'id': '8716fc26a',
            'pipeline': 'fake-pipe',
        })

        # Only sets things found in the identifiers, not random data.
        self.alt_collection.set_identifiers({
            'pipeline': 'something',
            'id': 'hello!',
            'bucket': 'something',
        })
        self.assertEqual(self.alt_collection._data, {
            'id': 'hello!',
            'pipeline': 'something',
        })

    def test_full_update_params(self):
        params = {
            'notify': True,
        }
        prepped = self.collection.full_update_params('create', params)
        self.assertEqual(prepped, {
            'global': True,
            'created': True,
            'notify': True,
        })

    def test_full_post_process(self):
        results = {
            'Id': '1872baf45',
            'Title': 'A pipe',
        }
        processed = self.collection.full_post_process('create', results)
        self.assertEqual(processed, {
            'Title': 'A pipe'
        })
        self.assertEqual(self.collection.created, True)

    def build_resource(self):
        # Reach in to fake some data.
        # We'll test proper behavior with the integration tests.
        self.session.cache.set_resource('test', 'Pipeline', Pipe)

        res_class = self.collection.build_resource({
            'test': 'data'
        })
        self.assertTrue(isinstance(res_class, Pipe))
        self.assertEqual(res_class.test, 'data')


class CollectionFactoryTestCase(unittest.TestCase):
    def setUp(self):
        super(CollectionFactoryTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.test_dirs = [
            os.path.join(os.path.dirname(__file__), 'test_data')
        ]
        self.test_loader = ResourceJSONLoader(self.test_dirs)
        self.cd = CollectionDetails(
            self.session,
            'test',
            'PipelineCollection',
            loader=self.test_loader
        )
        self.cf = CollectionFactory(
            session=self.session,
            loader=self.test_loader
        )

        # Fake in the class.
        self.session.cache.set_resource('test', 'Pipeline', FakePipeResource)

    def test_init(self):
        self.assertEqual(self.cf.session, self.session)
        self.assertTrue(isinstance(self.cf.loader, ResourceJSONLoader))
        self.assertEqual(self.cf.base_collection_class, Collection)
        self.assertEqual(self.cf.details_class, CollectionDetails)

        # Test overrides (invalid for actual usage).
        import boto3
        cf = CollectionFactory(
            loader=False,
            base_collection_class=PipeCollection,
            details_class=True
        )
        self.assertEqual(cf.session, boto3.session)
        self.assertEqual(cf.loader, False)
        self.assertEqual(cf.base_collection_class, PipeCollection)
        self.assertEqual(cf.details_class, True)

    def test_build_class_name(self):
        self.assertEqual(
            self.cf._build_class_name('PipelineCollection'),
            'PipelineCollection'
        )
        self.assertEqual(
            self.cf._build_class_name('TestName'),
            'TestName'
        )

    def test_build_methods(self):
        attrs = self.cf._build_methods(self.cd)
        self.assertEqual(len(attrs), 3)
        self.assertTrue('create' in attrs)
        self.assertTrue('each' in attrs)
        self.assertTrue('test_role' in attrs)

    def test_create_operation_method(self):
        class StubbyCollection(Collection):
            pass

        class StubbyResource(Resource):
            _details = ResourceDetails(
                self.session,
                'test',
                'Pipeline',
                loader=self.test_loader
            )

        op_method = self.cf._create_operation_method('create', {
            "api_name": "CreatePipeline"
        })
        self.assertEqual(op_method.__name__, 'create')
        self.assertEqual(op_method.__doc__, DEFAULT_DOCSTRING)

        # Assign it & call it.
        StubbyCollection._details = self.cd
        StubbyCollection.create = op_method
        StubbyCollection.change_resource(StubbyResource)
        sr = StubbyCollection(connection=FakeConn())
        fake_pipe = sr.create()
        self.assertEqual(fake_pipe.id, '1872baf45')
        self.assertEqual(fake_pipe.title, 'A pipe')

    def test_construct_for(self):
        col_class = self.cf.construct_for('test', 'PipelineCollection')
