# -*- coding: utf-8 -*-
import time

from boto3.core.session import Session

from tests import unittest


class IamConnectionTestCase(unittest.TestCase):
    def setUp(self):
        super(IamConnectionTestCase, self).setUp()
        self.iam_class = Session().get_connection('iam')
        self.iam = self.iam_class()

    def test_op_methods(self):
        ops = [
            'add_role_to_instance_profile',
            'add_user_to_group',
            'change_password',
            'create_access_key',
            'create_account_alias',
            'create_group',
            'create_instance_profile',
            'create_login_profile',
            'create_role',
            'create_user',
            'create_virtual_mfa_device',
            'deactivate_mfa_device',
            'delete_access_key',
            'delete_account_alias',
            'delete_account_password_policy',
            'delete_group',
            'delete_group_policy',
            'delete_instance_profile',
            'delete_login_profile',
            'delete_role',
            'delete_role_policy',
            'delete_server_certificate',
            'delete_signing_certificate',
            'delete_user',
            'delete_user_policy',
            'delete_virtual_mfa_device',
            'enable_mfa_device',
            'get_account_password_policy',
            'get_account_summary',
            'get_group',
            'get_group_policy',
            'get_instance_profile',
            'get_login_profile',
            'get_role',
            'get_role_policy',
            'get_server_certificate',
            'get_user',
            'get_user_policy',
            'list_access_keys',
            'list_account_aliases',
            'list_group_policies',
            'list_groups',
            'list_groups_for_user',
            'list_instance_profiles',
            'list_instance_profiles_for_role',
            'list_mfa_devices',
            'list_role_policies',
            'list_roles',
            'list_server_certificates',
            'list_signing_certificates',
            'list_user_policies',
            'list_users',
            'list_virtual_mfa_devices',
            'put_group_policy',
            'put_role_policy',
            'put_user_policy',
            'remove_role_from_instance_profile',
            'remove_user_from_group',
            'resync_mfa_device',
            'update_access_key',
            'update_account_password_policy',
            'update_assume_role_policy',
            'update_group',
            'update_login_profile',
            'update_server_certificate',
            'update_signing_certificate',
            'update_user',
            'upload_server_certificate',
            'upload_signing_certificate',
        ]

        for op_name in ops:
            self.assertTrue(
                hasattr(self.iam, op_name),
                msg="{0} is missing.".format(op_name)
            )
            self.assertTrue(
                callable(getattr(self.iam, op_name)),
                msg="{0} is not callable.".format(op_name)
            )

    def test_integration(self):
        user_name = 'test_user'
        group_name = 'test_group'

        resp = self.iam.create_group(
            group_name=group_name
        )

        self.addCleanup(
            self.iam.delete_group,
            group_name=group_name
        )

        resp = self.iam.list_groups()
        groups = [group['GroupName'] for group in resp['Groups']]
        self.assertTrue(group_name in groups)

        resp = self.iam.create_user(
            user_name=user_name
        )

        self.addCleanup(
            self.iam.delete_user,
            user_name=user_name
        )

        resp = self.iam.list_users()
        users = [user['UserName'] for user in resp['Users']]
        self.assertTrue(user_name in users)

        # Make sure there are no users.
        resp = self.iam.get_group(group_name=group_name)
        self.assertEqual(len(resp['Users']), 0)

        # Try adding the user to a group.
        resp = self.iam.add_user_to_group(
            user_name=user_name,
            group_name=group_name
        )
        self.addCleanup(
            self.iam.remove_user_from_group,
            user_name=user_name,
            group_name=group_name
        )

        resp = self.iam.get_group(group_name=group_name)
        self.assertEqual(len(resp['Users']), 1)
        self.assertTrue(resp['Users'][0]['UserName'], user_name)
