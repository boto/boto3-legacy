from boto3.core.service import Service

from tests import unittest


class TestObject(Service):
    service_name = 'to'
    _json_name = 'TestObject'


class BotoObjectTestCase(unittest.TestCase):
    def setUp(self):
        super(BotoObjectTestCase, self).setUp()


if __name__ == "__main__":
    unittest.main()
