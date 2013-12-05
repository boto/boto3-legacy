import boto3
from boto3.core.resources import Resource


PipelineCollection = boto3.session.get_collection(
    'elastictranscoder',
    'PipelineCollection'
)
PresetCollection = boto3.session.get_collection(
    'elastictranscoder',
    'PresetCollection'
)
JobCollection = boto3.session.get_collection(
    'elastictranscoder',
    'JobCollection'
)
Pipeline = boto3.session.get_resource('elastictranscoder', 'Pipeline')
Preset = boto3.session.get_resource('elastictranscoder', 'Preset')
Job = boto3.session.get_resource('elastictranscoder', 'Job')
