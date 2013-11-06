from boto3.core.exceptions import NoSuchMethod
from boto3.core.loader import ResourceJSONLoader
from boto3.utils.mangle import to_snake_case
from boto3.utils import six


class ResourceDetails(object):
    service_name = ''
    resource_name = ''
    session = None

    def __init__(self, session, service_name, resource_name, loader=None):
        super(ResourceDetails, self).__init__()
        self.session = session
        self.service_name = service_name
        self.resource_name = resource_name
        self.loader = loader
        self._api_versions = None
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
    def api_versions(self):
        self._api_versions = self._loaded_data.get('api_versions', '')
        return self._api_versions


class Resource(object):
    def __init__(self, connection=None):
        self._data = {}
        self._connection = connection

        # FIXME: Add more here as needed.

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

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]

        raise AttributeError(
            "{0} has no attribute {1}".format(
                self,
                name
            )
        )

    def __setattr__(self, name, value):
        if name in self._data:
            self._data[name] = value
            return

        super(Resource, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in self._data:
            del self._data[name]
            return

        super(Resource, self).__delattr__(name)


class ResourceFactory(object):
    """
    Generates the underlying ``Resource`` classes based off the ``ResourceJSON``
    included in the SDK.

    Typically used as a foundation to elaborate on.
    """
    default_data_dirs = [
        DEFAULT_RESOURCE_JSON_DIR,
    ]
    loader_class = ResourceJSONLoader

    def __init__(self, session=None, connection=None, data_dirs=None,
                 base_resource_class=Resource, loader=None,
                 details_class=ResourceDetails):
        self.session = session
        self.connection = connection
        self.data_dirs = data_dirs
        self.base_resource_class = base_resource_class
        self.loader = loader
        self.details_class = details_class

        if self.session is None:
            # Fallback to the default.
            import boto3
            self.session = boto3.session

        if self.data_dirs is None:
            self.data_dirs = self.default_data_dirs

    def construct_for(self, service_name, resource_name):
        loader = self.loader

        if loader is None:
            loader = self.loader_class(self.data_dirs)

        # FIXME: Resume here. We need to take the ``Resource`` name into account!
        details = self.details_class(
            self.session,
            service_name,
            resource_name,
            self.loader
        )

        attrs = {
            '_details': details,
        }

        # Determine what we should call it.
        klass_name = self._build_class_name(service_name)

        # Construct what the class ought to have on it.
        attrs.update(self._build_methods(details))

        # Create the class.
        return type(
            klass_name,
            (self.base_connection,),
            attrs
        )

    def _build_class_name(self, service_name):
        return '{0}Resource'.format(service_name.capitalize())

    def _build_methods(self, details):
        attrs = {}

        for method_name, op_data in details.service_data.items():
            # First we make expand then we defense it.
            # Construct a brand-new method & assign it on the class.
            attrs[method_name] = self._create_operation_method(method_name, op_data)

        return attrs
