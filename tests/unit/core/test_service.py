from boto3.core.service import ServiceDetails, ServiceFactory
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


class ServiceDetailsTestCase(unittest.TestCase):
    def setUp(self):
        super(ServiceDetailsTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.sd = ServiceDetails(
            service_name='test',
            session=self.session
        )

    def test_init(self):
        self.assertEqual(self.sd.service_name, 'test')
        self.assertEqual(self.sd.session, self.session)
        self.assertEqual(self.sd._api_version, None)
        self.assertEqual(self.sd._loaded_service_data, None)

    def test_service_data(self):
        self.assertEqual(self.sd._loaded_service_data, None)

        # Access the property. It should load the data, cache it & return it.
        self.assertEqual(len(self.sd.service_data), 2)

        self.assertNotEqual(self.sd._loaded_service_data, None)
        # Ensure the API version was cleared out as well.
        self.assertEqual(self.sd._api_version, None)

    def test_api_version(self):
        self.assertEqual(self.sd._api_version, None)

        # Access the property. It should load the data, cache it & return it.
        self.assertEqual(self.sd.api_version, '2013-08-23')

        self.assertEqual(self.sd._api_version, '2013-08-23')

    def test__introspect_service(self):
        service_data = self.sd._introspect_service(
            self.session.core_session,
            'test'
        )
        # We test the introspected data elsewhere, so it's enough that we
        # just check the necessary method names are here.
        self.assertEqual(sorted(list(service_data.keys())), [
            'create_queue',
            'delete_queue'
        ])


class ServiceFactoryTestCase(unittest.TestCase):
    def setUp(self):
        super(ServiceFactoryTestCase, self).setUp()
        self.session = Session(FakeSession(TestCoreService()))
        self.sf = ServiceFactory(session=self.session)
        self.test_service_class = self.sf.construct_for('test')

    def test__check_method_params(self):
        _cmp = self.test_service_class()._check_method_params
        op_params = [
            {
                'var_name': 'queue_name',
                'api_name': 'QueueName',
                'required': True,
                'type': 'string',
            },
            {
                'var_name': 'attributes',
                'api_name': 'Attributes',
                'required': False,
                'type': 'map',
            },
        ]
        # Missing the required ``queue_name`` parameter.
        self.assertRaises(TypeError, _cmp, op_params)
        self.assertRaises(TypeError, _cmp, op_params, attributes=1)

        # All required params present.
        self.assertEqual(_cmp(op_params, queue_name='boo'), None)
        self.assertEqual(_cmp(op_params, queue_name='boo', attributes=1), None)

    def test__build_service_params(self):
        _bsp = self.test_service_class()._build_service_params
        op_params = [
            {
                'var_name': 'queue_name',
                'api_name': 'QueueName',
                'required': True,
                'type': 'string',
            },
            {
                'var_name': 'attributes',
                'api_name': 'Attributes',
                'required': False,
                'type': 'map',
            },
        ]
        self.assertEqual(_bsp(op_params, queue_name='boo'), {
            'queue_name': 'boo',
        })
        self.assertEqual(_bsp(op_params, queue_name='boo', attributes=1), {
            'queue_name': 'boo',
            'attributes': 1,
        })

    def test__create_operation_method(self):
        func = self.sf._create_operation_method('test', {
            'method_name': 'test',
            'api_name': 'Test',
            'docs': 'This is a test.',
            'params': [],
            'output': True,
        })
        self.assertEqual(func.__name__, 'test')
        self.assertEqual(func.__doc__, 'This is a test.')

    def test__post_process_results(self):
        ppr = self.test_service_class()._post_process_results
        self.assertEqual(ppr('whatever', {}, (None, True)), True)
        self.assertEqual(ppr('whatever', {}, (None, False)), False)
        self.assertEqual(ppr('whatever', {}, (None, 'abc')), 'abc')
        self.assertEqual(ppr('whatever', {}, (None, ['abc', 1])), [
            'abc',
            1
        ])
        self.assertEqual(ppr('whatever', {}, (None, {'abc': 1})), {
            'abc': 1,
        })

    def test_integration(self):
        # Essentially testing ``_build_methods``.
        # This is a painful integration test. If the other methods don't work,
        # this will certainly fail.
        self.assertTrue(hasattr(self.test_service_class, 'create_queue'))
        self.assertTrue(hasattr(self.test_service_class, 'delete_queue'))

        ts = self.test_service_class()

        # Missing required parameters.
        self.assertRaises(TypeError, ts, 'create_queue')
        self.assertRaises(TypeError, ts, 'delete_queue')

        # Successful calls.
        self.assertEqual(ts.create_queue(queue_name='boo'), {
            'QueueUrl': 'http://example.com'
        })
        self.assertEqual(ts.delete_queue(queue_name='boo'), True)

    def test_late_binding(self):
        # If the ``ServiceDetails`` data changes, it should be reflected in
        # the dynamic methods.
        ts = self.test_service_class()

        # Successful calls.
        self.assertEqual(ts.create_queue(queue_name='boo'), {
            'QueueUrl': 'http://example.com'
        })

        # Now the required params change underneath us.
        # This is ugly/fragile, but also unlikely.
        sd = ts._details._loaded_service_data
        sd['create_queue']['params'][1]['required'] = True

        # Now this call should fail, since there's a new required parameter.
        self.assertRaises(TypeError, ts, 'create_queue')


if __name__ == "__main__":
    unittest.main()
