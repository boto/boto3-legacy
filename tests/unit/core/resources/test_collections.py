import mock

import boto3
from boto3.core.exceptions import ResourceError
from boto3.core.exceptions import IncorrectImportPath
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection
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


class FakeQueue(object):
    is_fake = True


class AnotherFakeQueue(object):
    is_another = True


class TestResourceCollection(ResourceCollection):
    resource_class = 'tests.unit.core.resources.test_collections.FakeQueue'
    valid_api_versions = [
        '2013-08-23',
    ]
    service_name = 'test'

    create = methods.CollectionMethod('create_queue')


class ResourceCollectionTestCase(unittest.TestCase):
    def setUp(self):
        super(ResourceCollectionTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.sf = ServiceFactory(session=self.session)
        self.conn_class = self.sf.construct_for('test')
        self.conn = self.conn_class()

    def tearDown(self):
        TestResourceCollection.resource_class = \
            'tests.unit.core.resources.test_collections.FakeQueue'
        super(ResourceCollectionTestCase, self).tearDown()

    def test_meta(self):
        # By this point, the ``TestResourceCollection`` class has already been
        # altered. Let's verify the important bits.
        self.assertEqual(
            TestResourceCollection.valid_api_versions[0],
            '2013-08-23'
        )
        self.assertEqual(
            TestResourceCollection.service_name,
            'test'
        )
        self.assertEqual(
            TestResourceCollection.resource_class,
            'tests.unit.core.resources.test_collections.FakeQueue'
        )
        # Make sure we picked up all the methods.
        self.assertEqual(sorted(TestResourceCollection._methods.keys()), [
            'create',
        ])
        # Make sure the method objects are safely ferreted away.
        self.assertTrue(isinstance(
            TestResourceCollection._methods['create'],
            methods.CollectionMethod
        ))
        # Make sure the metaclass sets the name.
        self.assertEqual(
            TestResourceCollection._methods['create'].name,
            'create'
        )
        # Check that the new methods have been created.
        self.assertTrue(hasattr(TestResourceCollection, 'create'))
        self.assertTrue(callable(TestResourceCollection.create))

    def test_init_defaults(self):
        # Without an explicit session or connection, should get defaults.
        # We need to mock part of this here, because we're dealing with a
        # non-real service.
        mpo = mock.patch.object
        sess = boto3.session

        with mpo(sess, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResourceCollection()
            self.assertEqual(test._session, sess)
            self.assertEqual(
                test._resource_class,
                'tests.unit.core.resources.test_collections.FakeQueue'
            )

        mock_conn.assert_called_once_with('test')

    def test_init_with_session(self):
        # With an explicit session.
        mpo = mock.patch.object
        session = Session()

        with mpo(session, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResourceCollection(session=session)
            self.assertEqual(test._session, session)
            self.assertEqual(
                test._resource_class,
                'tests.unit.core.resources.test_collections.FakeQueue'
            )

        mock_conn.assert_called_once_with('test')

    def test_init_with_connection(self):
        # With an explicit connection.
        mpo = mock.patch.object
        sess = boto3.session

        with mpo(sess, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResourceCollection(connection=self.conn)
            self.assertEqual(test._session, sess)
            self.assertEqual(
                test._resource_class,
                'tests.unit.core.resources.test_collections.FakeQueue'
            )

        # Make sure ``connect_to`` *isn't* called.
        self.assertEqual(mock_conn.call_count, 0)

    def test_init_with_resource_class(self):
        # With an overridden resource class.
        mpo = mock.patch.object
        sess = boto3.session

        with mpo(sess, 'connect_to', return_value=self.conn) as mock_conn:
            test = TestResourceCollection(
                connection=self.conn,
                resource_class=AnotherFakeQueue
            )
            self.assertEqual(test._session, sess)
            self.assertEqual(test._resource_class, AnotherFakeQueue)

        # Make sure ``connect_to`` *isn't* called.
        self.assertEqual(mock_conn.call_count, 0)

    def test_get_resource_class(self):
        test = TestResourceCollection(connection=self.conn)

        # With the string-type import path.
        cls = test.get_resource_class()
        self.assertTrue(cls.is_fake)

        # With an actual class.
        test = TestResourceCollection(
            connection=self.conn,
            resource_class=AnotherFakeQueue
        )
        cls = test.get_resource_class()
        self.assertTrue(cls.is_another)

        # Not found.
        with self.assertRaises(IncorrectImportPath):
            test = TestResourceCollection(
                connection=self.conn,
                resource_class='a.nonexistant.path.to.a.Resource'
            )
            cls = test.get_resource_class()

        # No class configured.
        with self.assertRaises(ResourceError):
            class NopeCollection(ResourceCollection):
                valid_api_versions = [
                    '2013-08-23'
                ]
                service_name = 'nope'

            test = NopeCollection(
                connection=self.conn
            )
            cls = test.get_resource_class()
