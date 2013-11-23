import botocore.session

from boto3.core.cache import ServiceCache
from boto3.core.constants import USER_AGENT_NAME, USER_AGENT_VERSION
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
        """
        Creates a ``Session`` instance.

        :param session: (Optional) Custom instantiated ``botocore`` instance.
            Useful if you have specific needs. If not present, a default
            ``Session`` will be created.
        :type session: <botocore.session.Session> instance

        :param connection_factory: (Optional) Specifies a custom
            ``ConnectionFactory`` to be used. Useful if you need to change how
            ``Connection`` objects are constructed by the session.
        :type connection_factory: <boto3.core.connection.ConnectionFactory>
            instance

        :param resource_factory: (Optional) Specifies a custom
            ``ResourceFactory`` to be used. Useful if you need to change how
            ``Resource`` objects are constructed by the session.
        :type resource_factory: <boto3.core.resources.ResourceFactory>
            instance

        :param collection_factory: (Optional) Specifies a custom
            ``CollectionFactory`` to be used. Useful if you need to change how
            ``Collection`` objects are constructed by the session.
        :type collection_factory: <boto3.core.collections.CollectionFactory>
            instance
        """
        super(Session, self).__init__()
        self.core_session = session
        self.connection_factory = connection_factory
        self.resource_factory = resource_factory
        self.collection_factory = collection_factory

        self.cache = self.cache_class()

        if not self.core_session:
            self.core_session = botocore.session.get_session()

        self.core_session.user_agent_name = USER_AGENT_NAME
        self.core_session.user_agent_version = USER_AGENT_VERSION

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
        """
        Returns a ``Connection`` **class** for a given service.

        :param service_name: A string that specifies the name of the desired
            service. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :rtype: <boto3.core.connection.Connection subclass>
        """
        try:
            return self.cache.get_connection(service_name)
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.connection_factory.construct_for(service_name)
        self.cache.set_connection(service_name, new_class)
        return new_class

    def get_resource(self, service_name, resource_name, base_class=None):
        """
        Returns a ``Resource`` **class** for a given service.

        :param service_name: A string that specifies the name of the desired
            service. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param resource_name: A string that specifies the name of the desired
            class. Ex. ``Queue``, ``Notification``, ``Table``, etc.
        :type resource_name: string

        :param base_class: (Optional) The base class of the object. Prevents
            "magically" loading the wrong class (one with a different base).
        :type base_class: class

        :rtype: <boto3.core.resources.Resource subclass>
        """
        try:
            return self.cache.get_resource(
                service_name,
                resource_name,
                base_class=base_class
            )
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.resource_factory.construct_for(
            service_name,
            resource_name,
            base_class=base_class
        )
        self.cache.set_resource(service_name, resource_name, new_class)
        return new_class

    def get_collection(self, service_name, collection_name, base_class=None):
        """
        Returns a ``Collection`` **class** for a given service.

        :param service_name: A string that specifies the name of the desired
            service. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param collection_name: A string that specifies the name of the desired
            class. Ex. ``QueueCollection``, ``NotificationCollection``,
            ``TableCollection``, etc.
        :type collection_name: string

        :param base_class: (Optional) The base class of the object. Prevents
            "magically" loading the wrong class (one with a different base).
        :type base_class: class

        :rtype: <boto3.core.collections.Collection subclass>
        """
        try:
            return self.cache.get_collection(
                service_name,
                collection_name,
                base_class=base_class
            )
        except NotCached:
            pass

        # We didn't find it. Construct it.
        new_class = self.collection_factory.construct_for(
            service_name,
            collection_name,
            base_class=base_class
        )
        self.cache.set_collection(service_name, collection_name, new_class)
        return new_class

    def connect_to(self, service_name, **kwargs):
        """
        Shortcut method to make instantiating the ``Connection`` classes
        easier.

        Forwards ``**kwargs`` like region, keys, etc. on to the constructor.

        :param service_name: A string that specifies the name of the desired
            service. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :rtype: <boto3.core.connection.Connection> instance
        """
        service_class = self.get_connection(service_name)
        return service_class.connect_to(**kwargs)

    def get_core_service(self, service_name):
        """
        Returns a ``botocore.service.Service``.

        Mostly an abstraction for the ``*Connection`` objects to get what
        they need for introspection.

        :param service_name: A string that specifies the name of the desired
            service. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :rtype: <botocore.service.Service subclass>
        """
        return self.core_session.get_service(service_name)
