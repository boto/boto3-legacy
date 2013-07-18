from boto3.base import BotoObject

from tests import unittest
from tests.unit.fakes import FakeSession


class TestObject(BotoObject):
    service_name = 'to'
    _json_name = 'TestObject'


class BotoObjectTestCase(unittest.TestCase):
    def setUp(self):
        super(BotoObjectTestCase, self).setUp()
        self.session = FakeSession()
        self.to = TestObject(self.session)

        # Make sure the class is clear.
        TestObject._reset()

    def test_getattribute(self):
        self.assertFalse(self.to.__class__._loaded)
        # Should cause a load, miss on the JSON lookup & find the instance
        # variable.
        self.assertEqual(self.to.service_name, 'to')
        self.assertTrue(self.to.__class__._loaded)

        self.assertEqual(self.to.create.__name__, 'create')
