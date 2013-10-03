from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection, Resource, Structure


class TopicCollection(ResourceCollection):
    resource_class = 'boto3.sns.resources.Topic'
    service_name = 'sns'
    valid_api_versions = [
        '2010-03-31',
    ]

    create = methods.CollectionMethod('create_topic')
    # FIXME: CONNUNDRUM! There is no "get_topic" API, but it's a thing users
    #        will want to do. Grump.
    get = methods.CollectionMethod('get_topic')


class Topic(Resource):
    valid_api_versions = [
        '2010-03-31',
    ]

    name = fields.BoundField('Name')
