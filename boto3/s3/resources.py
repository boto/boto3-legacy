from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection, Resource, Structure


class BucketCollection(ResourceCollection):
    resource_class = 'boto3.s3.resources.Bucket'
    service_name = 's3'
    valid_api_versions = [
        '2006-03-01',
    ]

    create = methods.CollectionMethod('CreateBucket')


class Bucket(Resource):
    valid_api_versions = [
        '2006-03-01',
    ]

    name = fields.BoundField('BucketName')


class KeyCollection(ResourceCollection):
    resource_class = 'boto3.s3.resources.Key'
    service_name = 's3'
    valid_api_versions = [
        '2006-03-01',
    ]

    create = methods.CollectionMethod('CreateKey')


class Key(Resource):
    valid_api_versions = [
        '2006-03-01',
    ]

    name = fields.BoundField('KeyName')
