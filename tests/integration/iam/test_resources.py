import time

import boto3
from boto3.iam.resources import GroupCollection, UserCollection
from boto3.iam.resources import Group, User

from tests import unittest


class IamIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        super(IamIntegrationTestCase, self).setUp()
        self.conn = boto3.session.connect_to('iam')

    def test_integration(self):
        user_name = 'test_user'
        group_name = 'test_group'

        group = GroupCollection(connection=self.conn).create(
            group_name=group_name
        )
        self.addCleanup(
            group.delete
        )

        groups = GroupCollection(connection=self.conn).each()
        group_names = [group.group_name for group in groups]
        self.assertTrue(group_name in group_names)

        user = UserCollection(connection=self.conn).create(
            user_name=user_name
        )
        self.addCleanup(
            user.delete
        )

        users = UserCollection(connection=self.conn).each()
        user_names = [user.user_name for user in users]
        self.assertTrue(user_name in user_names)

        # Make sure there are no users.
        group = Group(connection=self.conn, group_name=group_name)
        group.get()
        self.assertEqual(len(group.users), 0)

        # Try adding the user to a group.
        resp = group.add_user(
            user_name=user_name
        )
        self.addCleanup(
            group.remove_user,
            user_name=user_name
        )

        # Fetch the updated information
        group = Group(connection=self.conn, group_name=group_name)
        group.get()
        self.assertEqual(len(group.users), 1)
        self.assertTrue(group.users[0]['UserName'], user_name)
