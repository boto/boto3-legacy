from boto3.core.exceptions import NoSuchMethod
from boto3.core.loader import ResourceJSONLoader
from boto3.utils.mangle import to_snake_case
from boto3.utils import six


class CollectionDetails(object):
    service_name = ''
    collection_name = ''
    session = None

    def __init__(self, session, service_name, collection_name, loader=None):
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
        def _wrapper(self, *args, **kwargs):
            # If we don't have data, go load it.
            if self._loaded_data is None:
                self._loaded_data = self.loader[self.service_name]

            return func(self, *args, **kwargs)

        return _wrapper

    @property
    @requires_loaded
    def service_data(self):
        return self._loaded_data

    @property
    @requires_loaded
    def collection_data(self):
        return self._loaded_data['collections'][self.collection_name]

    @property
    @requires_loaded
    def api_versions(self):
        self._api_versions = self._loaded_data.get('api_versions', '')
        return self._api_versions

    @property
    @requires_loaded
    def resource(self):
        return self.collection_data.get('resource', None)


class Collection(object):
    def __init__(self, connection=None, **kwargs):
        self._connection = connection

        if self._connection is None:
            self._connection = self._details.session.connect_to(
                self._details.service_name
            )

    def __str__(self):
        return "{0}: {1} in {2}".format(
            self.__class__.__name__,
            self._details.service_name,
            self._connection.region_name
        )

    def full_update_params(self, conn_method_name, params):
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
        # By default, this is just a pass-through.
        return params

    def full_post_process(self, conn_method_name, result):
        result = self.post_process(conn_method_name, result)

        # We'll check for custom methods to do addition, specific work.
        custom_method_name = 'post_process_{0}'.format(conn_method_name)
        custom_method = getattr(self, custom_method_name, None)

        if custom_method:
            # Let the specific method further process the data.
            result = custom_method(result)

        return result

    def post_process(self, conn_method_name, result):
        # Mostly a hook for post-processing as needed.
        return result

    def build_resource(self, data):
        res_class = self._details.session.get_resource(
            self._details.service_name,
            self._details.resource
        )
        return res_class(**data)


class CollectionFactory(object):
    """
    Generates the underlying ``Collection`` classes based off the
    ``ResourceJSON`` included in the SDK.

    Typically used as a foundation to elaborate on.
    """
    loader_class = ResourceJSONLoader

    def __init__(self, session=None, loader=None,
                 base_collection_class=Collection,
                 details_class=CollectionDetails):
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

    def construct_for(self, service_name, collection_name):
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

        # Create the class.
        return type(
            klass_name,
            (self.base_collection_class,),
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

        _new_method.__name__ = method_name
        _new_method.__doc__ = op_data.get('docs', '')
        return _new_method
