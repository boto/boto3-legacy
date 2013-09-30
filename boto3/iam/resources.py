from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection, Resource, Structure


class RoleCollection(ResourceCollection):
    resource_class = 'boto3.iam.resources.Role'
    service_name = 'iam'
    valid_api_versions = [
        '2010-05-08',
    ]

    create = methods.CollectionMethod('CreateRole')


class Role(Resource):
    valid_api_versions = [
        '2010-05-08',
    ]

    name = fields.BoundField('RoleName')
