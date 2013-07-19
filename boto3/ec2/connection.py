import six

from boto3.core.service import ServiceMetaclass, Service


class EC2Connection(six.with_metaclass(ServiceMetaclass, Service)):
    service_name = 'ec2'
