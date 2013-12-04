from pprint import pprint

import boto3


template = """
# -*- coding: utf-8 -*-
from tests.integration.base import ConnectionTestCase
from tests import unittest


class {service_class_name}ConnectionTestCase(ConnectionTestCase, unittest.TestCase):
    service_name = '{service_name}'
    ops = [
        {expected_ops}
    ]

    def test_integration(self):
        {integration_body}
"""


class IntegrationTestBuilder(object):
    def __init__(self):
        self.service_name = None
        self.ops = []
        self.integ_tests = []

    def render(self):
        return template.format(
            service_class_name=self.service_name.lower().captialize(),
            service_name=self.service_name.lower(),
            expected_ops=self.build_ops(),
            integration_body=self.build_integration_body()
        )

    def create_connection(self):
        return boto3.session.connect_to(self.service_name)

    def build_ops(self):
        skips = [
            'connect_to',
            'region_name',
        ]

        for possible_op in dir(self.conn):
            if possible_op.startswith('_'):
                continue

            if possible_op in skips:
                continue

            if possible_op[0].isupper():
                continue

            self.ops.append(possible_op)

    def build_integration_body(self):
        pass

    def clean(self, string):
        return string.strip()

    def run(self):
        self.service_name = self.clean(input("Service name? (ex. s3, iam, ec2): "))
        self.conn = self.create_connection()
        print("  ``{0}`` available as ``self.conn``...".format(
            self.conn.__class__.__name__
        ))
        print("Use Ctrl+D to finalize the test case.")
        print()

        try:
            while True:
                code = self.clean(input('>>> '))

                resp = eval(code)
                pprint(resp)
                print()

                yes_no = self.clean(input("Keep this input/output for the test? (y/N): "))

                if yes_no.lower().startswith('y'):
                    self.integ_tests.append({
                        'code': code,
                        'result': resp
                    })

        except KeyboardInterrupt:
            pass

        print()
        print('=' * 80)
        print(self.render())


if __name__ == '__main__':
    itb = IntegrationTestBuilder()
    itb.run()
