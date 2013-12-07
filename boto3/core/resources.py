from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.exceptions import NoSuchMethod
from boto3.core.introspection import Introspection
from boto3.core.loader import ResourceJSONLoader
from boto3.utils.mangle import to_snake_case
from boto3.utils import six


class ResourceDetails(object):
    """
    A class that encapsulates the metadata about a given ``Resource``.

    Usually hangs off a ``Resource`` as ``Resource._details``.
    """
    service_name = ''
    resource_name = ''
    session = None

    def __init__(self, session, service_name, resource_name, loader=None):
        """
        Creates a ``ResourceDetails`` instance.

        :param session: The configured ``Session`` object to refer to.
        :type session: <class boto3.core.session.Session> instance

        :param service_name: The service a given ``Resource`` talks to. Ex.
            ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param resource_name: The name of the ``Resource``. Ex.
            ``Queue``, ``Notification``, ``Table``, etc.
        :type resource_name: string

        :param loader: (Optional) An instance of a ``ResourceJSONLoader`` class.
            This can be swapped with a different instance or with a completely
            different class with the same interface.
        :type loader: <class boto3.core.loader.ResourceJSONLoader> instance
        """
        super(ResourceDetails, self).__init__()
        self.session = session
        self.service_name = service_name
        self.resource_name = resource_name
        self.loader = loader
        self._api_version = None
        self._loaded_data = None

    def __str__(self):
        return u'<{0}: {1} - {2}>'.format(
            self.__class__.__name__,
            self.service_name,
            self.resource_name,
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
                self._loaded_data = self.loader.load(self.service_name)

            return func(self, *args, **kwargs)

        return _wrapper

    @property
    @requires_loaded
    def service_data(self):
        """
        Returns all introspected service data. This will include things like
        other resources/collections that are part of the service. Typically,
        using ``.resource_data`` is much more useful/relevant.

        If the data has been previously accessed, a memoized version of the
        data is returned.

        :returns: A dict of introspected service data
        :rtype: dict
        """
        return self._loaded_data

    @property
    @requires_loaded
    def resource_data(self):
        """
        Returns all introspected resource data.

        If the data has been previously accessed, a memoized version of the
        data is returned.

        :returns: A dict of introspected resource data
        :rtype: dict
        """
        return self._loaded_data['resources'][self.resource_name]

    @property
    @requires_loaded
    def api_version(self):
        """
        Returns the API version introspected from the resource data.
        This is useful in preventing mismatching API versions between the
        client code & service.

        If the data has been previously accessed, a memoized version of the
        API version is returned.

        :returns: The service's version
        :rtype: string
        """
        self._api_version = self._loaded_data.get('api_version', '')
        return self._api_version

    @property
    @requires_loaded
    def identifiers(self):
        """
        Returns the identifiers.

        If the data has been previously accessed, a memoized version of the
        variable name is returned.

        :returns: The identifiers
        :rtype: list
        """
        return self.resource_data['identifiers']

    @requires_loaded
    def result_key_for(self, op_name):
        """
        Checks for the presence of a ``result_key``, which defines what data
        should make up an instance.

        Returns ``None`` if there is no ``result_key``.

        :param op_name: The operation name to look for the ``result_key`` in.
        :type op_name: string

        :returns: The expected key to look for data within
        :rtype: string or None
        """
        ops = self.resource_data.get('operations', {})
        op = ops.get(op_name, {})
        key = op.get('result_key', None)
        return key

    @property
    @requires_loaded
    def relations(self):
        """
        Returns the relation data read from the resource data.

        Example data::

            {
                'name_on_the_instance_here': {
                    'class_type': 'resource',
                    'class': 'NameOfResource',
                    'required': True,
                    'rel_type': '1-M'
                }
            }

        :returns: The relation data, if any is present
        :rtype: dict
        """
        return self.resource_data.get('relations', {})


class Resource(object):
    """
    A common base class for all the ``Resource`` objects.
    """
    def __init__(self, connection=None, **kwargs):
        """
        Creates a new ``Resource`` instance.

        :param connection: (Optional) Specifies what connection to use.
            By default, this is a matching ``Connection`` subclass provided
            by the ``session`` (i.e. within S3, ``BucketResource`` would get a
            ``S3Connection`` from the session).
        :type connection: <class boto3.core.connection.Connection> **SUBCLASS**

        :param **kwargs: (Optional) Instance data to be specified on the
            instance itself.
        :type **kwargs: dict
        """
        # Tracks the *built* relations (actual instances).
        self._relations = {}
        # Tracks the scalar data on the resource.
        self._data = {}
        self._connection = connection

        for key, value in kwargs.items():
            self._data[key] = value

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

    def __getattr__(self, name):
        """
        Attempts to return either the related object or instance data for a
        given name if available.

        :param name: The instance data's name
        :type name: string
        """
        # Check to see if the thing being requested is a known relation.
        if name in self._details.relations:
            # Check if we already have built version.
            if not name in self._relations:
                # There's not a previously built object.
                # Lazily build it & assign it here.
                self._relations[name] = self.build_relation(name)

            return self._relations[name]

        if name in self._data:
            return self._data[name]

        raise AttributeError("No such attribute '{0}'".format(name))

    def _update_docstrings(self):
        """
        Runs through the operation methods & updates their docstrings if
        necessary.

        If the method has the default placeholder docstring, this will replace
        it with the docstring from the underlying connection.
        """
        ops = self._details.resource_data['operations']

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

            # We need to do detection here, because Py2 treats ``.__doc__``
            # as a special read-only attribute. :/
            if six.PY3:
                meth.__doc__ = conn_meth.__doc__
            else:
                meth.__func__.__doc__ = conn_meth.__doc__

    def get_identifiers(self):
        """
        Returns the identifier(s) (if present) from the instance data.

        The identifier name(s) is/are determined from the ``ResourceDetails``
        instance hanging off the class itself.

        :returns: All the identifier information
        :rtype: dict
        """
        data = {}

        for id_info in self._details.identifiers:
            var_name = id_info['var_name']
            data[var_name] = self._data.get(var_name)

        return data

    def set_identifiers(self, data):
        """
        Sets the identifier(s) within the instance data.

        The identifier name(s) is/are determined from the ``ResourceDetails``
        instance hanging off the class itself.

        :param data: The value(s) to be set.
        :param data: dict
        """
        for id_info in self._details.identifiers:
            var_name = id_info['var_name']
            self._data[var_name] = data.get(var_name)

        # FIXME: This needs to likely kick off invalidating/rebuilding
        #        relations.
        #        For now, just remove them all. This is potentially inefficient
        #        but is nicely lazy if we don't need them & prevents stale data
        #        for the moment.
        self._relations = {}

    def build_relation(self, name, klass=None):
        """
        Constructs a related ``Resource`` or ``Collection``.

        This allows for construction of classes with information prepopulated
        from what the current instance has. This enables syntax like::

            bucket = Bucket(bucket='some-bucket-name')

            for obj in bucket.objects.each():
                print(obj.key)

        :param name: The name of the relation from the ResourceJSON
        :type name: string

        :param klass: (Optional) An overridable class to construct. Typically
            only useful if you need a custom subclass used in place of what
            boto3 provides.
        :type klass: class

        :returns: An instantiated related object
        """
        try:
            rel_data = self._details.relations[name]
        except KeyError:
            msg = "No such relation named '{0}'.".format(name)
            raise NoRelation(msg)

        if klass is None:
            # This is the typical case, where we're not explicitly given a
            # class to build with. Hit the session & look up what we should
            # be loading.
            if rel_data['class_type'] == 'collection':
                klass = self._details.session.get_collection(
                    self._details.service_name,
                    rel_data['class']
                )
            elif rel_data['class_type'] == 'resource':
                klass = self._details.session.get_resource(
                    self._details.service_name,
                    rel_data['class']
                )
            else:
                msg = "Unknown class '{0}' for '{1}'.".format(
                    rel_data['class_type'],
                    name
                )
                raise NoRelation(msg)

        # Instantiate & return it.
        kwargs = {}
        # Just populating identifiers is enough for the 1-M case.
        kwargs.update(self.get_identifiers())

        if rel_data.get('rel_type', '1-M') == '1-1':
            # FIXME: If it's not a collection, we might have some instance data
            #        (i.e. ``bucket``) in ``self._data`` to populate as well.
            #        This seems like a can of worms, so ignore for the moment.
            pass

        return klass(connection=self._connection, **kwargs)

    def full_update_params(self, conn_method_name, params):
        """
        When a API method on the resource is called, this goes through the
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

        By default, this just ensures the identifier data in in the parameters,
        so that the user doesn't have to provide it.

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
        # By default, this just sets the identifier info.
        # We use ``var_name`` instead of ``api_name``. Because botocore.
        params.update(self.get_identifiers())
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

        By default, this does nothing, just passing through the ``result``.

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
        return result

    def post_process_get(self, result):
        """
        Given an object with identifiers, fetches the data for that object
        from the service.

        This alters the data on the object itself & simply passes through what
        was received.

        :param result: The response data
        :type result: dict

        :returns: The unmodified response data
        """
        if not hasattr(result, 'items'):
            # If it's not a dict, give up & just return whatever you get.
            return result

        # We need to possibly drill into the response & get out the data here.
        # Check for a result key.
        result_key = self._details.result_key_for('get')

        if not result_key:
            # There's no result_key. Just use the top-level data.
            data = result
        else:
            data = result[result_key]

        for key, value in data.items():
            self._data[to_snake_case(key)] = value

        return result


class ResourceFactory(object):
    """
    Generates the underlying ``Resource`` classes based off the ``ResourceJSON``
    included in the SDK.

    Usage::

        >>> rf = ResourceFactory()
        >>> Bucket = rf.construct_for('s3', 'Bucket')

    """
    loader_class = ResourceJSONLoader

    def __init__(self, session=None, loader=None,
                 base_resource_class=Resource,
                 details_class=ResourceDetails):
        """
        Creates a new ``ResourceFactory`` instance.

        :param session: The ``Session`` the factory should use.
        :type session: <class boto3.session.Session> instance

        :param loader: (Optional) An instance of a ``ResourceJSONLoader`` class.
            This can be swapped with a different instance or with a completely
            different class with the same interface.
            By default, this is ``boto3.core.loader.default_loader``.
        :type loader: <class boto3.core.loader.ResourceJSONLoader> instance

        :param base_resource_class: (Optional) The base class to use when creating
            the resource. By default, this is ``Resource``, but should
            you need to globally change the behavior of all resources,
            you'd simply specify this to provide your own class.
        :type base_resource_class: <class boto3.core.resources.Resource>

        :param details_class: (Optional) The metadata class used to store things
            like service name & data. By default, this is ``ResourceDetails``,
            but should you need to globally change the behavior (perhaps
            modifying how the resource data is returned), you simply provide
            your own class here.
        :type details_class: <class boto3.core.resources.ResourceDetails>
        """
        self.session = session
        self.loader = loader
        self.base_resource_class = base_resource_class
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

    def construct_for(self, service_name, resource_name, base_class=None):
        """
        Builds a new, specialized ``Resource`` subclass as part of a given
        service.

        This will load the ``ResourceJSON``, determine the correct
        mappings/methods & constructs a brand new class with those methods on
        it.

        :param service_name: The name of the service to construct a resource
            for. Ex. ``sqs``, ``sns``, ``dynamodb``, etc.
        :type service_name: string

        :param resource_name: The name of the ``Resource``. Ex.
            ``Queue``, ``Notification``, ``Table``, etc.
        :type resource_name: string

        :returns: A new resource class for that service
        """
        details = self.details_class(
            self.session,
            service_name,
            resource_name,
            loader=self.loader
        )

        attrs = {
            '_details': details,
        }

        # Determine what we should call it.
        klass_name = self._build_class_name(resource_name)

        # Construct what the class ought to have on it.
        attrs.update(self._build_methods(details))

        if base_class is None:
            base_class = self.base_resource_class

        # Create the class.
        return type(
            klass_name,
            (base_class,),
            attrs
        )

    def _build_class_name(self, resource_name):
        return resource_name

    def _build_methods(self, details):
        attrs = {}
        ops = details.resource_data.get('operations', {}).items()

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

        _new_method.__name__ = method_name
        _new_method.__doc__ = DEFAULT_DOCSTRING
        return _new_method
