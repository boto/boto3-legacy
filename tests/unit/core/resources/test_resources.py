import mock

import boto3
from boto3.core.exceptions import APIVersionMismatchError
from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import Resource
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
            'DeleteQueue',
            " <p>Deletes a queue.</p>\n ",
            params=[
                FakeParam('QueueName', required=True, ptype='string'),
            ],
            output=True,
            result=(None, True)
        ),
    ]


class TestResource(Resource):
    valid_api_versions = [
        '2013-08-23',
    ]
    service_name = 'test'

    name = fields.BoundField('QueueName')
    url = fields.BoundField('QueueUrl', required=False)

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
