import boto3
from boto3.core.resources import Resource


class GroupCustomizations(Resource):
    def update_params_add_user(self, params):
        params.update(self.get_identifiers())
        return params

    def update_params_remove_user(self, params):
        params.update(self.get_identifiers())
        return params


# FIXME: These should be just sane defaults, but they are configured at
#        import-time. :/
AccessKeyCollection = boto3.session.get_collection(
    'iam',
    'AccessKeyCollection'
)
AccountAliasCollection = boto3.session.get_collection(
    'iam',
    'AccountAliasCollection'
)
GroupCollection = boto3.session.get_collection(
    'iam',
    'GroupCollection'
)
InstanceProfileCollection = boto3.session.get_collection(
    'iam',
    'InstanceProfileCollection'
)
LoginProfileCollection = boto3.session.get_collection(
    'iam',
    'LoginProfileCollection'
)
RoleCollection = boto3.session.get_collection('iam', 'RoleCollection')
UserCollection = boto3.session.get_collection('iam', 'UserCollection')
VirtualMFADeviceCollection = boto3.session.get_collection(
    'iam',
    'VirtualMFADeviceCollection'
)
AccessKey = boto3.session.get_resource('iam', 'AccessKey')
AccountAlias = boto3.session.get_resource('iam', 'AccountAlias')
Group = boto3.session.get_resource(
    'iam',
    'Group',
    base_class=GroupCustomizations
)
InstanceProfile = boto3.session.get_resource('iam', 'InstanceProfile')
LoginProfile = boto3.session.get_resource('iam', 'LoginProfile')
Role = boto3.session.get_resource('iam', 'Role')
User = boto3.session.get_resource('iam', 'User')
VirtualMFADevice = boto3.session.get_resource('iam', 'VirtualMFADevice')
