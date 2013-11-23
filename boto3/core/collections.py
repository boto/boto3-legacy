from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.exceptions import NoSuchMethod
from boto3.core.loader import ResourceJSONLoader
from boto3.utils.mangle import to_snake_case
from boto3.utils import six


class CollectionDetails(object):
    """
    A class that encapsulates the metadata about a given ``Collection``.

    Usually hangs off a ``Collection`` as ``Collection._details``.
    """
    service_name = ''
    collection_name = ''
    session = None

    def __init__(self, session, service_name, collection_name, loader=None):
        """
        Creates a ``CollectionDetails`` instance.

        :param session: The configured ``Session`` object to refer to.
        :type session: <class boto3.core.session.Session> instance

        :param service_name: The service a given ``Collection`` talks to. Ex.
            ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param collection_name: The name of the ``Collection``. Ex.
            ``Queue``, ``Notification``, ``Table``, etc.
        :type collection_name: string

        :param loader: (Optional) An instance of a ``ResourceJSONLoader`` class.
            This can be swapped with a different instance or with a completely
            different class with the same interface.
        :type loader: <class boto3.core.loader.ResourceJSONLoader> instance
        """
        super(CollectionDetails, self).__init__()
        self.session = session
        self.service_name = service_name
        self.collection_name = collection_name
        self.loader = loader
        self._api_versions = None
        self._loaded_data = None

    def __str__(self):
        return u'<{0}: {1} - {2}>'.format(
            self.__class__.__name__,
            self.service_name,
            self.collection_name,
            self.api_version
        )

    # Kinda ugly (method within a class definition, but not static/classmethod)
    # but depends on internal state. Grump.
    def requires_loaded(func):
        """
        A decorator to ensure the resource data is loaded.
        """
        def _wrapper(self, *args, **kwargs):
            # If we don't have data, go load it.
            if self._loaded_data is None:
                self._loaded_data = self.loader[self.service_name]

            return func(self, *args, **kwargs)

        return _wrapper

    @property
    @requires_loaded
    def service_data(self):
        """
        Returns all introspected service data. This will include things like
        other resources/collections that are part of the service. Typically,
        using ``.collection_data`` is much more useful/relevant.

        If the data has been previously accessed, a memoized version of the
        data is returned.

        :returns: A dict of introspected service data
        :rtype: dict
        """
        return self._loaded_data

    @property
    @requires_loaded
    def collection_data(self):
        """
        Returns all introspected collection data.

        If the data has been previously accessed, a memoized version of the
        data is returned.

        :returns: A dict of introspected collection data
        :rtype: dict
        """
        return self._loaded_data['collections'][self.collection_name]

    @property
    @requires_loaded
    def api_versions(self):
        """
        Returns the API version(s) introspected from the collection data. This
        is a list of all versions of the API to which this data can be used.
        This is useful in preventing mismatching API versions between the
        client code & service.

        If the data has been previously accessed, a memoized version of the
        API versions is returned.

        :returns: The service's versions
        :rtype: list of strings
        """
        self._api_versions = self._loaded_data.get('api_versions', '')
        return self._api_versions

    @property
    @requires_loaded
    def resource(self):
        """
        Returns the ``Resource`` to which this collection should be mapped.

        If the data has been previously accessed, a memoized version of the
        resource name is returned.

        :returns: The resource name
        :rtype: string
        """
        return self.collection_data.get('resource', None)


class Collection(object):
    """
    A common base class for all the ``Collection`` objects.
    """
    _res_class = None

    def __init__(self, connection=None, **kwargs):
        """
        Creates a new ``Collection`` instance.

        :param connection: (Optional) Specifies what connection to use.
            By default, this is a matching ``Connection`` subclass provided
            by the ``session`` (i.e. within S3, ``BucketCollection`` would get a
            ``S3Connection`` from the session).
        :type connection: <class boto3.core.connection.Connection> **SUBCLASS**

        :param **kwargs: (Optional) Reserved for future use.
        :type **kwargs: dict
        """
        self._connection = connection

        if self._connection is None:
            self._connection = self._details.session.connect_to(
                self._details.service_name
            )

        # Now that we have a connection, we can update docstrings.
        self._update_docstrings()

    def __str__(self):
        return "{0}: {1} in {2}".format(
            self.__class__.__name__,
            self._details.service_name,
            self._connection.region_name
        )

    @classmethod
    def change_resource(cls, resource_class):
        """
        Updates the default ``Resource`` class created when the ``Collection``
        is returning instances.

        Default behavior (without calling this method) is that the class
        will return whatever the ``session`` can provide.

        :param resource_class: The new ``Resource`` class to use during
            construction.
        :type resource_class: class
        """
        cls._res_class = resource_class

    def _update_docstrings(self):
        """
        Runs through the operation methods & updates their docstrings if
        necessary.

        If the method has the default placeholder docstring, this will replace
        it with the docstring from the underlying connection.
        """
        ops = self._details.collection_data['operations']

        for method_name in ops.keys():
            meth = getattr(self.__class__, method_name, None)

            if not meth:
                continue

            if meth.__doc__ != DEFAULT_DOCSTRING:
                # It already has a custom docstring. Leave it alone.
                continue

            # Needs updating. So there's at least *something* vaguely useful
            # there, use the docstring from the underlying ``Connection``
            # method.
            # FIXME: We need to figure out a way to make this more useful, if
            #        possible.
            api_name = ops[method_name]['api_name']
            conn_meth = getattr(self._connection, to_snake_case(api_name))
            meth.__doc__ = conn_meth.__doc__

    def full_update_params(self, conn_method_name, params):
        """
        When a API method on the collection is called, this goes through the
        params & run a series of hooks to allow for updating those parameters.

        Typically, this method is **NOT** call by the user. However, the user
        may wish to define other methods (i.e. ``update_params`` to work with
        multiple parameters at once or ``update_params_METHOD_NAME`` to
        manipulate a single parameter) on their class, which this method
        will call.

        :param conn_method_name: The name of the underlying connection method
            about to be called. Typically, this is a "snake_cased" variant of
            the API name (i.e. ``update_bucket`` in place of ``UpdateBucket``).
        :type conn_method_name: string

        :param params: A dictionary of all the key/value pairs passed to the
            method. This dictionary is transformed by this call into the final
            params to be passed to the underlying connection.
        :type params: dict
        """
        # We'll check for custom methods to do addition, specific work.
        custom_method_name = 'update_params_{0}'.format(conn_method_name)
        custom_method = getattr(self, custom_method_name, None)

        if custom_method:
            # Let the specific method further process the data.
            params = custom_method(params)

        # Now that all the method-specific data is there, apply any further
        # service-wide changes here.
        params = self.update_params(conn_method_name, params)
        return params

    def update_params(self, conn_method_name, params):
        """
        A hook to allow manipulation of multiple parameters at once.

        By default, this does nothing & simply passes through the parameters.

        You can override/extend this method (typically on your subclass)
        to do additional checks, pre-populate values or remove unwanted data.

        :param conn_method_name: The name of the underlying connection method
            about to be called. Typically, this is a "snake_cased" variant of
            the API name (i.e. ``update_bucket`` in place of ``UpdateBucket``).
        :type conn_method_name: string

        :param params: A dictionary of all the key/value pairs passed to the
            method. This dictionary is transformed by this call into the final
            params to be passed to the underlying connection.
        :type params: dict
        """
        # By default, this is just a pass-through.
        return params

    def full_post_process(self, conn_method_name, result):
        """
        When a response from an API method call is received, this goes through
        the returned data & run a series of hooks to allow for handling that
        data.

        Typically, this method is **NOT** call by the user. However, the user
        may wish to define other methods (i.e. ``post_process`` to work with
        all the data at once or ``post_process_METHOD_NAME`` to
        handle a single piece of data) on their class, which this method
        will call.

        :param conn_method_name: The name of the underlying connection method
            about to be called. Typically, this is a "snake_cased" variant of
            the API name (i.e. ``update_bucket`` in place of ``UpdateBucket``).
        :type conn_method_name: string

        :param result: A dictionary of all the key/value pairs passed back
            from the API (server-side). This dictionary is transformed by this
            call into the final data to be passed back to the user.
        :type result: dict
        """
        result = self.post_process(conn_method_name, result)

        # We'll check for custom methods to do addition, specific work.
        custom_method_name = 'post_process_{0}'.format(conn_method_name)
        custom_method = getattr(self, custom_method_name, None)

        if custom_method:
            # Let the specific method further process the data.
            result = custom_method(result)

        return result

    def post_process(self, conn_method_name, result):
        """
        A hook to allow manipulation of the entire returned data at once.

        By default, this goes through & (shallowly) snake-cases all of the
        keys, so that the result is friendlier to use from Python.

        You can override/extend this method (typically on your subclass)
        to do additional checks, alter the result or remove unwanted data.

        :param conn_method_name: The name of the underlying connection method
            about to be called. Typically, this is a "snake_cased" variant of
            the API name (i.e. ``update_bucket`` in place of ``UpdateBucket``).
        :type conn_method_name: string

        :param result: A dictionary of all the key/value pairs passed back
            from the API (server-side). This dictionary is transformed by this
            call into the final data to be passed back to the user.
        :type result: dict
        """
        # Mostly a hook for post-processing as needed.
        snaked = {}

        # TODO: This is shallow (only the top-level of keys).
        #       We may need a deeper conversion.
        for key, value in result.items():
            snaked[to_snake_case(key)] = value

        return snaked

    def post_process_create(self, result):
        """
        An example of the ``post_process`` extensions, this returns an instance
        of the ``Resource`` created (rather than just a bag of data).

        :param result: The full data handed back from the API.
        :type result: dict

        :returns: A ``Resource`` subclass
        """
        return self.build_resource(result)

    def post_process_get(self, result):
        """
        An example of the ``post_process`` extensions, this returns an instance
        of the ``Resource`` created (rather than just a bag of data).

        :param result: The full data handed back from the API.
        :type result: dict

        :returns: A ``Resource`` subclass
        """
        return self.build_resource(result)

    def build_resource(self, data):
        """
        Given some data, builds the correct/matching ``Resource`` subclass
        for the ``Collection``. Useful in things like ``create`` & ``get``.

        :param result: The data for an instance handed back from the API.
        :type result: dict

        :returns: A ``Resource`` subclass
        """
        if self._res_class is None:
            self._res_class = self._details.session.get_resource(
                self._details.service_name,
                self._details.resource
            )

        return self._res_class(connection=self._connection, **data)


class CollectionFactory(object):
    """
    Generates the underlying ``Collection`` classes based off the
    ``ResourceJSON`` included in the SDK.

    Usage::

        >>> cf = CollectionFactory()
        >>> BucketCollection = cf.construct_for('s3', 'BucketCollection')

    """
    loader_class = ResourceJSONLoader

    def __init__(self, session=None, loader=None,
                 base_collection_class=Collection,
                 details_class=CollectionDetails):
        """
        Creates a new ``CollectionFactory`` instance.

        :param session: The ``Session`` the factory should use.
        :type session: <class boto3.session.Session> instance

        :param loader: (Optional) An instance of a ``ResourceJSONLoader`` class.
            This can be swapped with a different instance or with a completely
            different class with the same interface.
            By default, this is ``boto3.core.loader.default_loader``.
        :type loader: <class boto3.core.loader.ResourceJSONLoader> instance

        :param base_collection_class: (Optional) The base class to use when
            creating the collection. By default, this is ``Collection``, but
            should you need to globally change the behavior of all collections,
            you'd simply specify this to provide your own class.
        :type base_collection_class: <class boto3.core.collections.Collection>

        :param details_class: (Optional) The metadata class used to store things
            like service name & data. By default, this is ``CollectionDetails``,
            but should you need to globally change the behavior (perhaps
            modifying how the collection data is returned), you simply provide
            your own class here.
        :type details_class: <class boto3.core.collections.CollectionDetails>
        """
        self.session = session
        self.loader = loader
        self.base_collection_class = base_collection_class
        self.details_class = details_class

        if self.session is None:
            # Fallback to the default.
            import boto3
            self.session = boto3.session

        if self.loader is None:
            import boto3.core.loader
            self.loader = boto3.core.loader.default_loader

    def __str__(self):
        return self.__class__.__name__

    def construct_for(self, service_name, collection_name, base_class=None):
        """
        Builds a new, specialized ``Collection`` subclass as part of a given
        service.

        This will load the ``ResourceJSON``, determine the correct
        mappings/methods & constructs a brand new class with those methods on
        it.

        :param service_name: The name of the service to construct a resource
            for. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param collection_name: The name of the ``Collection``. Ex.
            ``QueueCollection``, ``NotificationCollection``,
            ``TableCollection``, etc.
        :type collection_name: string

        :returns: A new collection class for that service
        """
        details = self.details_class(
            self.session,
            service_name,
            collection_name,
            loader=self.loader
        )

        attrs = {
            '_details': details,
        }

        # Determine what we should call it.
        klass_name = self._build_class_name(collection_name)

        # Construct what the class ought to have on it.
        attrs.update(self._build_methods(details))

        if base_class is None:
            base_class = self.base_collection_class

        # Create the class.
        return type(
            klass_name,
            (base_class,),
            attrs
        )

    def _build_class_name(self, collection_name):
        return collection_name

    def _build_methods(self, details):
        attrs = {}
        ops = details.collection_data.get('operations', {}).items()

        for method_name, op_data in ops:
            attrs[method_name] = self._create_operation_method(
                method_name,
                op_data
            )

        return attrs

    def _create_operation_method(factory_self, method_name, op_data):
        # Determine the correct name for the method.
        # This is because the method names will be standardized across
        # resources, so we'll have to lean on the ``api_name`` to figure out
        # what the correct underlying method name on the ``Connection`` should
        # be.
        # Map -> map -> unmap -> remap -> map :/
        conn_method_name = to_snake_case(op_data['api_name'])

        if not six.PY3:
            method_name = str(method_name)

        def _new_method(self, **kwargs):
            params = self.full_update_params(method_name, kwargs)
            method = getattr(self._connection, conn_method_name, None)

            if not method:
                msg = "Introspected method named '{0}' not available on " + \
                      "the connection."
                raise NoSuchMethod(msg.format(conn_method_name))

            result = method(**params)
            return self.full_post_process(method_name, result)

        # Get the (possibly overridden) docs from the op_data.
        # If it's not there **or** is ``null``, populate with the default
        # docstring.
        docs = op_data.get('docs', None)

        if docs is None:
            docs = DEFAULT_DOCSTRING

        _new_method.__name__ = method_name
        _new_method.__doc__ = docs
        return _new_method
