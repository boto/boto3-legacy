import botocore.session

from boto3.core.connection import ConnectionFactory


class Session(object):
    """
    Stores all the state for a given ``boto3`` session.

    Can dynamically create all the various ``Connection`` classes.

    Usage::

        >>> from boto3.core.session import Session
        >>> session = Session()
        >>> sqs_conn = session.connect_to_region('sqs', region_name='us-west-2')

    """
    conn_classes = {}

    def __init__(self, session=None, factory=None):
        super(Session, self).__init__()
        self.core_session = session
        self.factory = factory

        if not self.core_session:
            self.core_session = botocore.session.get_session()

        if not self.factory:
            self.factory = ConnectionFactory(session=self)

    def get_service(self, service_name):
        classes = self.__class__.conn_classes

        # FIXME: We may need a way to track multiple versions of a service
        #        within the same running codebase. For now, just the services
        #        themselves are fine.
        if service_name in classes:
            return classes[service_name]

        # We didn't find it. Construct it.
        new_class = self.factory.construct_for(service_name)
        classes[service_name] = new_class
        return new_class

    def connect_to(self, service_name, **kwargs):
        """
        Shortcut method to make instantiating the ``Connection`` classes
        easier.

        Forwards ``kwargs`` like region, keys, etc. on to the constructor.
        """
        service_class = self.get_service(service_name)
        return service_class.connect_to(**kwargs)

    def get_core_service(self, service_name):
        """
        Returns a ``botocore.service.Service``.

        Mostly an abstraction for the ``*Connection`` objects to get what
        they need for introspection.
        """
        return self.core_session.get_service(service_name)

    @classmethod
    def _reset(cls):
        cls.conn_classes = {}
