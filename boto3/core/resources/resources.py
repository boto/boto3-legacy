from boto3.core.resources.base import ResourceBase
from boto3.utils import OrderedDict
from boto3.utils import six


class ResourceMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Check if we're dealing with the base class.
        # If so, don't run the rest of the metaclass.
        if attrs.get('service_name', None) is None:
            return super(ResourceMetaclass, cls).__new__(
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
            'service_name': orig_attrs.pop('service_name'),
            'structures_to_use': orig_attrs.pop('structures_to_use', []),
            'fields': OrderedDict(),
            '_methods': OrderedDict(),
        }

        # We keep the objects as is, stowing them on the instance (think
        # ``self._methods``), then construct wrapper methods that delegate
        # off to them.
        # Iterate & pick out the fields/methods for construction.
        # Note: We're duck-typing (looking at an attribute) because calling
        #       ``isinstance(...)`` is pretty frail & could break badly for
        #       other yet-to-be-created-or-known subclasses. Quack.
        for attr_name, value in orig_attrs.items():
            if getattr(value, 'is_field', False):
                # It's a field. Weird, right?
                attrs['fields'][attr_name] = value
                # Make sure the instance knows what the parent thinks it's
                # called.
                setattr(value, 'name', attr_name)
            elif getattr(value, 'is_method', False):
                attrs['_methods'][attr_name] = value
                setattr(value, 'name', attr_name)

        klass = super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)

        # Once we're done constructing the base object, go back & add on the
        # methods.
        # We do this after the fact so that we can let the ``Resource`` (or
        # similar) class handle the construction of the methods.
        # This avoids further metaclass hackery & puts the subclass in control,
        # rather than embedding that logic here.
        for attr_name, method in klass._methods.items():
            method.setup_on_resource(klass)

        return klass


@six.add_metaclass(ResourceMetaclass)
class Resource(ResourceBase):
    service_name = None
    structures_to_use = []

    def __init__(self, session=None, connection=None):
        super(Resource, self).__init__()
        self._session = session
        self._connection = connection
        self._data = {}

        if self._session is None:
            import boto3
            self._session = boto3.session

        if self._connection is None:
            self._connection = self._session.connect_to(self.service_name)

        self._update_docstrings()
        self._check_api_version()

    def __str__(self):
        return u'<{0}>'.format(
            self.__class__.__name__
        )

    def __getattr__(self, name):
        # Python didn't find it hanging off the class already, so it might
        # be field data. Delegate to the field if present.
        if name in self.fields:
            return self.fields[name].get_python(self)

        raise AttributeError(
            "'{0}' object has no attribute '{1}'".format(
                self.__class__.__name__,
                name
            )
        )

    def __setattr__(self, name, value):
        # Check to see if it's a value for a known field first.
        # If so, let the field set the data.
        if name in self.fields:
            self.fields[name].set_python(self, value)
            return

        # Must be regular assignment.
        super(Resource, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in self.fields:
            self.fields[name].delete(self)
            return

        # Must be regular deletion.
        super(Resource, self).__delattr__(name)
