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

        # FIXME: This needs to return objects.
        resp = GroupCollection(connection=self.conn).each()
        groups = [group['GroupName'] for group in resp['groups']]
        self.assertTrue(group_name in groups)

        user = UserCollection(connection=self.conn).create(
            user_name=user_name
        )

        self.addCleanup(
            user.delete
        )

        # FIXME: This needs to return objects.
        resp = UserCollection(connection=self.conn).each()
        users = [user['UserName'] for user in resp['users']]
        self.assertTrue(user_name in users)

        # Make sure there are no users.
        # FIXME: This fails for a couple reasons.
        #        1. The identifier isn't present in the response, so we don't
        #           extract the data & set it on the instance.
        #        2. The 'Users' list is *outside* the ``Group`` data. Grump.
        group = Group(group_name=group_name).get()
        self.assertEqual(len(group['Users']), 0)

        # Try adding the user to a group.
        resp = group.add_user(
            user_name=user_name
        )
        self.addCleanup(
            group.remove_user,
            user_name=user_name
        )

        group = Group(group_name=group_name).get()
        self.assertEqual(len(group.users), 0)
        self.assertTrue(group.users[0]['UserName'], user_name)
