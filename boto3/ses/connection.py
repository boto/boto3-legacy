import six

from boto3.core.service import ServiceMetaclass, Service


class S3Connection(six.with_metaclass(ServiceMetaclass, Service)):
    service_name = 's3'
