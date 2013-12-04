# -*- coding: utf-8 -*-
import time

from boto3.core.session import Session

from tests import unittest


class ConnectionTestCase(object):
    """
    A base class to make testing connections a little less verbose/more
    standard.

    This automatically sets up a connection object for the service
    (``self.conn``) & runs a test to ensure the connection has all the right
    API methods.

    Usage::

        from tests.integration.base import ConnectionTestCase
        from tests import unittest


        class MyConnTest(ConnectionTestCase, unittest.TestCase):
            service_name = 's3'
            ops = [
                'abort_multipart_upload',
                'complete_multipart_upload',
                'copy_object',
                'create_bucket',
                'create_multipart_upload',
                # ...
            ]

            # You can add your own test methods here...

    """
    service_name = None
    ops = []

    def setUp(self):
        super(ConnectionTestCase, self).setUp()
        self.session = Session()
        self.conn_class = self.session.get_connection(self.service_name)
        self.conn = self.conn_class()

    def test_op_methods(self):
        if not self.service_name:
            return

        if not len(self.ops):
            self.fail("There are no expected Connection methods supplied.")

        for op_name in self.ops:
            self.assertTrue(
                hasattr(self.conn, op_name),
                msg="{0} is missing.".format(op_name)
            )
            self.assertTrue(
                callable(getattr(self.conn, op_name)),
                msg="{0} is not callable.".format(op_name)
            )
