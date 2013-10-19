import mock

from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.constants import NO_NAME
from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.constants import NO_RESOURCE
from boto3.core.exceptions import NoNameProvidedError
from boto3.core.exceptions import NoResourceAttachedError
from boto3.core.resources.fields import BaseField
from boto3.core.resources.methods import BaseMethod
from boto3.core.resources.methods import InstanceMethod
from boto3.core.resources.methods import CollectionMethod
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
            'DeleteQueue',
            " <p>Deletes a queue.</p>\n ",
            params=[
                FakeParam('QueueName', required=True, ptype='string'),
            ],
            output=True,
            result=(None, True)
        ),
    ]


class FakeStructure(object):
    possible_paths = [
        'Messages',
        'Queue.Message',
    ]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeResource(object):
    fields = {
        'name': BaseField('QueueName'),
        'url': BaseField('QueueUrl', required=False),
    }
    structures_to_use = [
        FakeStructure,
    ]


class BaseMethodTestCase(unittest.TestCase):
    def setUp(self):
        super(BaseMethodTestCase, self).setUp()
        self.fake_resource = FakeResource()
        self.create_method = BaseMethod('create_queue')
        self.create_method.resource = self.fake_resource

        self.session = Session(FakeSession(TestCoreService()))
        self.sf = ServiceFactory(session=self.session)
        self.conn_class = self.sf.construct_for('test')
        self.conn = self.conn_class()

    def remove_added_method(self, method_name):
        delattr(FakeResource, method_name)

    def test_incorrect_setup(self):
        bare = BaseMethod()

        with self.assertRaises(NoNameProvidedError):
            bare.check_name()

        with self.assertRaises(NoResourceAttachedError):
            bare.check_resource_class()

    def test_setup_on_resource(self):
        bare = BaseMethod()

        with self.assertRaises(NotImplementedError):
            bare.setup_on_resource(FakeResource)

    def test_teardown_on_resource(self):
        self.create_method.name = 'create_thing'
        setattr(FakeResource, 'create_thing', True)
        self.assertTrue(FakeResource.create_thing)

        self.create_method.teardown_on_resource(FakeResource)

        with self.assertRaises(AttributeError):
            FakeResource.create_thing

    def test_get_expected_parameters(self):
        base = BaseMethod('create_queue')
        self.assertEqual(base.get_expected_parameters(self.conn), [
            {
                'type': 'string',
                'required': True,
                'api_name': 'QueueName',
                'var_name': 'queue_name'
            },
            {
                'type': 'map',
                'required': False,
                'api_name': 'Attributes',
                'var_name': 'attributes'
            }
        ])

        # We should get different parameters for a different operation.
        base = BaseMethod('delete_queue')
        self.assertEqual(base.get_expected_parameters(self.conn), [
            {
                'type': 'string',
                'required': True,
                'api_name': 'QueueName',
                'var_name': 'queue_name'
            },
        ])

    def test_get_bound_params(self):
        expected = [
            {
                'type': 'string',
                'required': True,
                'api_name': 'QueueName',
                'var_name': 'queue_name'
            },
            {
                'type': 'map',
                'required': False,
                'api_name': 'Attributes',
                'var_name': 'attributes'
            }
        ]
        # First, with no data on the resource.
        self.assertEqual(self.create_method.get_bound_params(expected), {
            'queue_name': NOTHING_PROVIDED,
        })

        # Set data.
        self.fake_resource.name = 'whatever'
        self.assertEqual(self.create_method.get_bound_params(expected), {
            'queue_name': 'whatever',
        })

    def test_check_required_params(self):
        # FIXME: For now, this does nothing in the implementation. If we remove
        #        it there, we should remove it here.
        self.assertEqual(self.create_method.check_required_params({}, {}), None)

    def test_update_bound_params_from_api(self):
        def del_new_attr(name):
            try:
                delattr(self.fake_resource, name)
            except AttributeError:
                pass

        # They shouldn't be there.
        self.assertEqual(getattr(self.fake_resource, 'name', None), None)
        self.assertEqual(getattr(self.fake_resource, 'url', None), None)
        self.addCleanup(del_new_attr, 'name')
        self.addCleanup(del_new_attr, 'url')

        # Get data back from an API call & update.
        self.create_method.update_bound_params_from_api({
            'QueueName': 'whatever',
        })

        self.assertEqual(getattr(self.fake_resource, 'name', None), 'whatever')
        self.assertEqual(getattr(self.fake_resource, 'url', None), None)

        # New data.
        self.create_method.update_bound_params_from_api({
            'QueueUrl': '/197246/whatever',
        })

        self.assertEqual(getattr(self.fake_resource, 'name', None), 'whatever')
        self.assertEqual(
            getattr(self.fake_resource, 'url', None),
            '/197246/whatever'
        )

    def test_post_process_results(self):
        # If we don't recognize anything, just pass it through.
        self.assertEqual(
            self.create_method.post_process_results({
                'this': 'is a test',
            }),
            {
                'this': 'is a test',
            }
        )

        # We find a single structure.
        result = self.create_method.post_process_results({
            'this': 'is a test',
            'Queue': {
                'Message': {
                    'body': 'o hai',
                }
            }
        })
        self.assertEqual(result['Queue']['Message'].body, 'o hai')

        # We find a list at a different key.
        result = self.create_method.post_process_results({
            'this': 'is a test',
            'Messages': [
                {
                    'body': 'o hai',
                },
                {
                    'body': 'another',
                }
            ]
        })
        self.assertEqual(len(result['Messages']), 2)
        self.assertEqual(result['Messages'][0].body, 'o hai')
        self.assertEqual(result['Messages'][1].body, 'another')

    def test_call(self):
        base = BaseMethod('create_queue')
        base.name = 'create_method'
        base.resource = self.fake_resource
        mpo = mock.patch.object

        # Just the passed args.
        ret = {'QueueUrl': '/test-queue'}

        with mpo(self.conn, 'create_queue', return_value=ret) as mock_conn:
            results = base.call(self.conn, queue_name='test-queue')
            self.assertEqual(
                getattr(self.fake_resource, 'name', None),
                None
            )
            self.assertEqual(
                getattr(self.fake_resource, 'url', None),
                '/test-queue'
            )
            self.assertEqual(results, {
                'QueueUrl': '/test-queue',
            })

        mock_conn.assert_called_once_with(queue_name='test-queue')

        # With the kwargs to be partially applied.
        base = BaseMethod('create_queue', limit=2, queue_name='unseen')
        base.name = 'create_method'
        base.resource = self.fake_resource
        ret = {'QueueUrl': '/test-queue', 'CreateCount': 1}

        with mpo(self.conn, 'create_queue', return_value=ret) as mock_conn:
            results = base.call(self.conn, queue_name='test-queue')
            self.assertEqual(
                getattr(self.fake_resource, 'name', None),
                None
            )
            self.assertEqual(
                getattr(self.fake_resource, 'url', None),
                '/test-queue'
            )
            self.assertEqual(results, {
                'CreateCount': 1,
                'QueueUrl': '/test-queue',
            })

        mock_conn.assert_called_once_with(limit=2, queue_name='test-queue')

        # With bound params.
        base = BaseMethod('create_queue', limit=2)
        base.name = 'create_method'
        base.resource = self.fake_resource
        self.fake_resource.name = 'whatever'
        ret = {
            'QueueUrl': '/whatever-queue',
            # This should update the instance's ``name``.
            'QueueName': 'Whatever',
        }

        with mpo(self.conn, 'create_queue', return_value=ret) as mock_conn:
            results = base.call(self.conn)
            self.assertEqual(
                getattr(self.fake_resource, 'name', None),
                'Whatever'
            )
            self.assertEqual(
                getattr(self.fake_resource, 'url', None),
                '/whatever-queue'
            )
            self.assertEqual(results, {
                'QueueName': 'Whatever',
                'QueueUrl': '/whatever-queue',
            })

        mock_conn.assert_called_once_with(limit=2, queue_name='whatever')

    def test_update_docstring(self):
        # Setup to fake a method we can actually test.
        def create_thing(self, *args, **kwargs):
            return True

        fake_resource = FakeResource()
        fake_resource._connection = self.conn
        create_method = BaseMethod('create_queue')
        create_method.name = 'create_thing'
        setattr(FakeResource, 'create_thing', create_thing)
        self.addCleanup(self.remove_added_method, 'create_thing')

        # Shouldn't have a docstring.
        self.assertEqual(fake_resource.create_thing.__doc__, None)

        create_method.update_docstring(fake_resource)

        # Shouldn't have a docstring.
        self.assertEqual(
            fake_resource.create_thing.__doc__,
            ' <p>Creates a queue.</p>\n '
        )


class InstanceMethodTestCase(unittest.TestCase):
    def remove_added_method(self, method_name):
        delattr(FakeResource, method_name)

    def test_init(self):
        inst = InstanceMethod('something')
        self.assertTrue(inst.is_instance_method)

    def test_setup_on_resource(self):
        inst = InstanceMethod('something')
        inst.name = 'something'
        self.assertFalse(hasattr(FakeResource, 'something'))
        self.addCleanup(self.remove_added_method, 'something')

        inst.setup_on_resource(FakeResource)
        self.assertTrue(hasattr(FakeResource, 'something'))
        the_method = getattr(FakeResource, 'something')
        self.assertEqual(the_method.__name__, 'something')
        self.assertEqual(the_method.__doc__, DEFAULT_DOCSTRING)


class CollectionMethodTestCase(unittest.TestCase):
    def remove_added_method(self, method_name):
        delattr(FakeResource, method_name)

    def test_init(self):
        coll = CollectionMethod('something')
        self.assertTrue(coll.is_collection_method)

    def test_setup_on_resource(self):
        coll = CollectionMethod('something')
        coll.name = 'something'
        self.assertFalse(hasattr(FakeResource, 'something'))
        self.addCleanup(self.remove_added_method, 'something')

        coll.setup_on_resource(FakeResource)
        self.assertTrue(hasattr(FakeResource, 'something'))
        the_method = getattr(FakeResource, 'something')
        self.assertEqual(the_method.__name__, 'something')
        self.assertEqual(the_method.__doc__, DEFAULT_DOCSTRING)
