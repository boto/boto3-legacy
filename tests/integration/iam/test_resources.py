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

        # FIXME: The data on this user object is wrong (one level too high).
        group = GroupCollection(connection=self.conn).create(
            group_name=group_name
        )
        # To deal with the above FIXME, for now, get the user again.
        # Remove this once the above is fixed.
        group = Group(connection=self.conn, group_name=group_name)
        group.get()

        self.addCleanup(
            group.delete
        )

        # FIXME: This needs to return objects.
        resp = GroupCollection(connection=self.conn).each()
        groups = [group['GroupName'] for group in resp['groups']]
        self.assertTrue(group_name in groups)

        # FIXME: The data on this user object is wrong (one level too high).
        user = UserCollection(connection=self.conn).create(
            user_name=user_name
        )
        # To deal with the above FIXME, for now, get the user again.
        # Remove this once the above is fixed.
        user = User(connection=self.conn, user_name=user_name)
        user.get()

        self.addCleanup(
            user.delete
        )

        # FIXME: This needs to return objects.
        resp = UserCollection(connection=self.conn).each()
        users = [user['UserName'] for user in resp['users']]
        self.assertTrue(user_name in users)

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
