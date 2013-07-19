import six

from boto3.core.service import ServiceMetaclass, Service


class SQSConnection(six.with_metaclass(ServiceMetaclass, Service)):
    service_name = 'sqs'
