from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.constants import NO_NAME
from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.constants import NO_RESOURCE
from boto3.core.exceptions import NoNameProvidedError
from boto3.core.exceptions import NoResourceAttachedError
from boto3.core.resources.methods import BaseMethod
from boto3.core.resources.methods import InstanceMethod
from boto3.core.session import Session

from tests import unittest


class TestResource(object):
    pass


class BaseMethodTestCase(unittest.TestCase):
    def setUp(self):
        super(BaseMethodTestCase, self).setUp()
        self.test_resource = TestResource()
        self.create_method = BaseMethod('create_thing')
        # Used for testing, not against live endpoints.

        self.sqs_conn =

    def test_incorrect_setup(self):
        bare = BaseMethod()

        with self.assertRaises(NoNameProvidedError):
            bare.check_name()

        with self.assertRaises(NoResourceAttachedError):
            bare.check_resource_class()

    def test_setup_on_resource(self):
        bare = BaseMethod()

        with self.assertRaises(NotImplementedError):
            bare.setup_on_resource(TestResource)

    def test_teardown_on_resource(self):
        self.create_method.name = 'create_thing'
        setattr(TestResource, 'create_thing', True)
        self.assertTrue(TestResource.create_thing)

        self.create_method.teardown_on_resource(TestResource)

        with self.assertRaises(AttributeError):
            TestResource.create_thing

    def test_get_expected_parameters(self):
        pass

    def test_get_bound_params(self):
        pass

    def test_check_required_params(self):
        pass

    def test_update_bound_params_from_api(self):
        pass

    def test_post_process_results(self):
        pass

    def test_call(self):
        pass

    def test_update_docstring(self):
        pass


class InstanceMethodTestCase(unittest.TestCase):
    pass
