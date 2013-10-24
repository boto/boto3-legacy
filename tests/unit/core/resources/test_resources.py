import mock

import boto3
from boto3.core.exceptions import APIVersionMismatchError
from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import Resource
from boto3.core.resources import Structure
from boto3.core.service import ServiceFactory
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


class TestMessage(Structure):
    valid_api_versions = [
        '2013-08-23',
    ]
    possible_paths = [
        'Messages',
    ]

    message_id = fields.BoundField('MessageId', required=False)
    body = fields.BoundField('Body')
    md5 = fields.BoundField('MD5OfBody', required=False)
    attributes = fields.ListBoundField('Attributes', data_class=None, required=False)
    receipt_handle = fields.BoundField('ReceiptHandle', required=False)


class TestResource(Resource):
    valid_api_versions = [
        '2013-08-23',
    ]
    service_name = 'test'
    structures_to_use = [
        TestMessage,
    ]

    name = fields.BoundField('QueueName')
    url = fields.BoundField('QueueUrl', required=False)

    receive = methods.InstanceMethod('receive_message')
    send = methods.InstanceMethod('send_message', message_type='json')
    delete = methods.InstanceMethod('delete_queue')


class ResourceTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.sf = ServiceFactory(session=self.session)
        self.conn_class = self.sf.construct_for('test')
        self.conn = self.conn_class()

    def test_meta(self):
        # By this point, the ``TestResource`` class has already been altered.
        # Let's verify the important bits.
        self.assertEqual(TestResource.valid_api_versions[0], '2013-08-23')
        self.assertEqual(TestResource.service_name, 'test')
        # Ensure we've got all the fields.
        self.assertEqual(sorted(TestResource.fields.keys()), [
            'name',
            'url',
        ])
        # Make sure the metaclass sets the name.
        self.assertEqual(TestResource.fields['url'].name, 'url')
        # Make sure we picked up all the methods.
        self.assertEqual(sorted(TestResource._methods.keys()), [
            'delete',
            'receive',
            'send',
        ])
        # Make sure the method objects are safely ferreted away.
        self.assertTrue(isinstance(
            TestResource._methods['delete'],
            methods.InstanceMethod
        ))
        # Make sure the metaclass sets the name.
        self.assertEqual(TestResource._methods['delete'].name, 'delete')
        # Check that the new methods have been created.
        self.assertTrue(hasattr(TestResource, 'delete'))
        self.assertTrue(callable(TestResource.delete))
        self.assertTrue(hasattr(TestResource, 'delete'))
        self.assertTrue(callable(TestResource.send))

    def test_init_defaults(self):
        # Without an explicit session or connection, should get defaults.
        # We need to mock part of this here, because we're dealing with a
        # non-real service.
        mpo = mock.patch.object
        sess = boto3.session

        with mpo(sess, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResource()
            self.assertEqual(test._session, sess)
            self.assertEqual(test._data, {})

        mock_conn.assert_called_once_with('test')

    def test_init_with_session(self):
        # With an explicit session.
        mpo = mock.patch.object
        session = Session()

        with mpo(session, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResource(session=session)
            self.assertEqual(test._session, session)
            self.assertEqual(test._data, {})

        mock_conn.assert_called_once_with('test')

    def test_init_with_connection(self):
        # With an explicit connection.
        mpo = mock.patch.object
        sess = boto3.session

        with mpo(sess, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResource(connection=self.conn)
            self.assertEqual(test._session, sess)
            self.assertEqual(test._data, {})

        # Make sure ``connect_to`` *isn't* called.
        self.assertEqual(mock_conn.call_count, 0)

    def test_update_docstrings(self):
        # In the definition above, there are no docstrings.
        # Just make sure they got populated.
        test = TestResource(connection=self.conn)
        self.assertEqual(
            TestResource.delete.__doc__,
            ' <p>Deletes a queue.</p>\n '
        )
        self.assertEqual(
            TestResource.send.__doc__,
            ' <p>Sends a message to a queue.</p>\n '
        )

    def test_check_api_version(self):
        # With an acceptable API version.
        test = TestResource(connection=self.conn)
        test._check_api_version()

        # With a bad API version
        test.valid_api_versions = [
            'nopenopenope',
        ]

        with self.assertRaises(APIVersionMismatchError):
            test._check_api_version()

    def test_getattr(self):
        test = TestResource(connection=self.conn)

        # A plain old attribute.
        test.not_a_field = True
        self.assertEqual(test.not_a_field, True)

        # A field.
        test._data['name'] = 'a-test'
        self.assertEqual(test.name, 'a-test')

        # Not found.
        with self.assertRaises(AttributeError):
            test.not_anything_known

    def test_setattr(self):
        test = TestResource(connection=self.conn)

        # A field.
        self.assertEqual(test._data, {})
        test.name = 'a-test'
        self.assertEqual(test._data, {
            'name': 'a-test',
        })

        # A plain old attribute.
        test.now_known_but_poorly_understood = True
        self.assertEqual(test._data, {
            'name': 'a-test',
        })
        self.assertEqual(test.now_known_but_poorly_understood, True)

    def test_delattr(self):
        test = TestResource(connection=self.conn)

        # A field.
        test._data['name'] = 'a-test'
        self.assertTrue('name' in test._data)
        del test.name
        self.assertFalse('name' in test._data)

        # A plain old attribute.
        test.now_known_but_poorly_understood = True
        self.assertTrue(hasattr(test, 'now_known_but_poorly_understood'))
        del test.now_known_but_poorly_understood
        self.assertFalse(hasattr(test, 'now_known_but_poorly_understood'))

    def test_response_parsing(self):
        test = TestResource(connection=self.conn)
        test.url = '/a-test/url'

        result = test.receive()

        self.assertEqual(len(result['Messages']), 2)
        msg_0 = result['Messages'][0]
        msg_1 = result['Messages'][1]
        self.assertTrue(isinstance(msg_0, TestMessage))
        self.assertTrue(isinstance(msg_1, TestMessage))
        self.assertEqual(msg_0.message_id, 'msg-12345')
        self.assertEqual(msg_0.body, 'Hello, world!')
        self.assertEqual(msg_0.md5, '6cd3556deb0da54bca060b4c39479839')
        self.assertEqual(msg_1.message_id, 'msg-12346')
        self.assertEqual(msg_1.body, 'Another message!')
        self.assertEqual(msg_1.md5, '6cd355')

    def test_full_prepare(self):
        test = TestResource(connection=self.conn)
        test.name = 'test'
        test.url = '/1b2a98376/test'

        data = test.full_prepare()
        self.assertEqual(data, {
            'name': 'test',
            'url': '/1b2a98376/test',
        })

    def test_prepare_failed(self):
        test = TestResource(connection=self.conn)
        test.name = 'going-away'
        test.url = '/1c298c73/going-away'

        # Delete a required key.
        del test.name

        with self.assertRaises(KeyError):
            data = test.full_prepare()

    def test_full_populate(self):
        test = TestResource(connection=self.conn)
        test.full_populate({
            'QueueName': 'another',
            'QueueUrl': '/98731bda/another',
            'Ignored': 'whatever',
        })
        self.assertEqual(test._data, {
            'url': '/98731bda/another',
            'name': 'another',
        })
