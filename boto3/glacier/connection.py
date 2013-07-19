import six

from boto3.core.service import ServiceMetaclass, Service


class GlacierConnection(six.with_metaclass(ServiceMetaclass, Service)):
    service_name = 'glacier'
