import botocore.session

from boto3.core.cache import ServiceCache
from boto3.core.exceptions import NotCached


class Session(object):
    """
    Stores all the state for a given ``boto3`` session.

    Can dynamically create all the various ``Connection`` classes.

    Usage::

        >>> from boto3.core.session import Session
        >>> session = Session()
        >>> sqs_conn = session.connect_to('sqs', region_name='us-west-2')

    """
    cache_class = ServiceCache

    def __init__(self, session=None, connection_factory=None,
                 resource_factory=None, collection_factory=None):
        super(Session, self).__init__()
        self.core_session = session
        self.connection_factory = connection_factory
        self.resource_factory = resource_factory
        self.collection_factory = collection_factory

        self.cache = self.cache_class()

        if not self.core_session:
            self.core_session = botocore.session.get_session()

        if not self.connection_factory:
            from boto3.core.connection import ConnectionFactory
            self.connection_factory = ConnectionFactory(session=self)

        if not self.resource_factory:
            from boto3.core.resources import ResourceFactory
            self.resource_factory = ResourceFactory(session=self)

        if not self.collection_factory:
            from boto3.core.collections import CollectionFactory
            self.collection_factory = CollectionFactory(session=self)

    def get_connection(self, service_name):
        try:
            return self.cache.get_connection(service_name)
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.connection_factory.construct_for(service_name)
        self.cache.set_connection(service_name, new_class)
        return new_class

    def get_resource(self, service_name, resource_name):
        try:
            return self.cache.get_resource(service_name)
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.resource_factory.construct_for(
            service_name,
            resource_name
        )
        self.cache.set_resource(service_name, new_class)
        return new_class

    def get_collection(self, service_name, collection_name):
        try:
            return self.cache.get_connection(service_name)
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.collection_factory.construct_for(
            service_name,
            collection_name
        )
        self.cache.set_collection(service_name, new_class)
        return new_class

    def connect_to(self, service_name, **kwargs):
        """
        Shortcut method to make instantiating the ``Connection`` classes
        easier.

        Forwards ``kwargs`` like region, keys, etc. on to the constructor.
        """
        service_class = self.get_connection(service_name)
        return service_class.connect_to(**kwargs)

    def get_core_service(self, service_name):
        """
        Returns a ``botocore.service.Service``.

        Mostly an abstraction for the ``*Connection`` objects to get what
        they need for introspection.
        """
        return self.core_session.get_service(service_name)
