from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.constants import NO_NAME
from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.constants import NO_RESOURCE
from boto3.core.exceptions import NoNameProvidedError
from boto3.core.exceptions import NoResourceAttachedError
from boto3.core.resources.fields import BaseField
from boto3.core.resources.methods import BaseMethod
from boto3.core.resources.methods import InstanceMethod
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


class FakeResource(object):
    fields = {
        'name': BaseField('QueueName'),
        'url': BaseField('QueueUrl', required=False),
    }


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
        # FIXME: For now, thise does nothing in the implementation. If we remove
        #        it there, we should remove it here.
        self.assertEqual(self.create_method.check_required_params({}, {}), None)

    def test_update_bound_params_from_api(self):
        # They shouldn't be there.
        self.assertEqual(getattr(self.fake_resource, 'name', None), None)
        self.assertEqual(getattr(self.fake_resource, 'url', None), None)

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
        pass

    def test_call(self):
        pass

    def test_update_docstring(self):
        pass


class InstanceMethodTestCase(unittest.TestCase):
    pass
