from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection, Resource, Structure


class PipelineCollection(ResourceCollection):
    resource_class = 'boto3.elastictranscoder.resources.Pipeline'
    service_name = 'transcoder'
    valid_api_versions = [
        '2012-09-25',
    ]

    create = methods.CollectionMethod('create_pipeline')
    get = methods.CollectionMethod('get_pipeline')


class Pipeline(Resource):
    valid_api_versions = [
        '2012-09-25',
    ]

    name = fields.BoundField('PipelineName')


class JobCollection(ResourceCollection):
    resource_class = 'boto3.elastictranscoder.resources.Job'
    service_name = 'transcoder'
    valid_api_versions = [
        '2012-09-25',
    ]

    create = methods.CollectionMethod('create_job')
    get = methods.CollectionMethod('get_job')


class Job(Resource):
    valid_api_versions = [
        '2012-09-25',
    ]

    name = fields.BoundField('JobName')
