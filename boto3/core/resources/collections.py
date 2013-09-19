from botocore.compat import OrderedDict
from botocore.compat import six

from boto3.core.exceptions import ResourceError
from boto3.core.resources.base import ResourceBase
from boto3.utils.import_utils import import_class


# TODO: This is almost identical to the ``ResourceMetaclass``.
#       DRY-ing it up would be nice, but difference between
#       ``resource_class`` and ``fields/collection`` makes it difficult.
class ResourceCollectionMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Check if we're dealing with the base class.
        # If so, don't run the rest of the metaclass.
        if attrs.get('service_name', None) is None:
            return super(ResourceCollectionMetaclass, cls).__new__(
                cls,
                name,
                bases,
                attrs
            )

        # Preserve what we originally got.
        orig_attrs = attrs

        # Build the new attributes we're actually going to construct the
        # class with.
        attrs = {
            'valid_api_versions': orig_attrs.pop('valid_api_versions', []),
            'resource_class': orig_attrs.pop('resource_class', None),
            '_methods': OrderedDict(),
        }

        # We keep the objects as is, stowing them on the instance (think
        # ``self._methods``), then construct wrapper methods that delegate
        # off to them.
        # Iterate & pick out the methods for construction.
        # Note: We're duck-typing (looking at an attribute) because calling
        #       ``isinstance(...)`` is pretty frail & could break badly for
        #       other yet-to-be-created-or-known subclasses. Quack.
        for attr_name, value in orig_attrs.items():
            if getattr(value, 'is_method', False):
                attrs['_methods'][attr_name] = value
                setattr(value, 'name', attr_name)

        klass = super(ResourceCollectionMetaclass, cls).__new__(
            cls,
            name,
            bases,
            attrs
        )

        # Once we're done constructing the base object, go back & add on the
        # methods.
        # We do this after the fact so that we can let the ``Resource`` (or
        # similar) class handle the construction of the methods.
        # This avoids further metaclass hackery & puts the subclass in control,
        # rather than embedding that logic here.
        for attr_name, method in klass._methods.items():
            method.setup_on_resource(klass)

        return klass


@six.add_metaclass(ResourceCollectionMetaclass)
class ResourceCollection(ResourceBase):
    resource_class = None
    service_name = None

    def __init__(self, session, connection=None, resource_class=None):
        super(ResourceCollection, self).__init__()
        self._session = session
        self._connection = connection

        if self._connection is None:
            klass = self._session.get_service(self.service_name)
            self._connection = klass()

        if resource_class is not None:
            self._resource_class = resource_class

        self._update_docstrings()
        self._check_api_version()

    def __str__(self):
        return u'<{0} for {1}>'.format(
            self.__class__.__name__,
            self.get_resource_class().__name__
        )

    def get_resource_class(self):
        if self.resource_class is None:
            raise ResourceError(
                "No resource_class configured for '{0}.".format(
                    self.__class__.__name__
                )
            )

        if isinstance(self.resource_class, six.string_types):
            # We've got a path. Try to import it.
            self.resource_class = import_class(self.resource_class)

        return self.resource_class
