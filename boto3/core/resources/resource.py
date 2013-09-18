import six

from botocore.compat import OrderedDict

from boto3.core.exceptions import ResourceError


class ResourceMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name in ['NewBase', 'Resource']:
            # Grumble grumble six grumble.
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
            'fields': OrderedDict(),
            '_class_methods': OrderedDict(),
            '_instance_methods': OrderedDict(),
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
                if getattr(value, 'is_class_method', False):
                    attrs['_class_methods'][attr_name] = value
                    setattr(value, 'name', attr_name)
                elif getattr(value, 'is_instance_method', False):
                    attrs['_instance_methods'][attr_name] = value
                    setattr(value, 'name', attr_name)

        klass = super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)

        # Once we're done constructing the base object, go back & add on the
        # methods.
        #
        # We do this after the fact so that we can let the ``Resource`` (or
        # similar) class handle the construction of the methods.
        #
        # This avoids further metaclass hackery & puts the subclass in control,
        # rather than embedding that logic here.
        for attr_name, method in klass._instance_methods.items():
            method.setup_on_resource(klass)

        for attr_name, method in klass._class_methods.items():
            method.setup_on_resource(klass)

        return klass


class Resource(six.with_metaclass(ResourceMetaclass)):
    # Subclasses should always specify this & list out the API versions
    # it supports.
    valid_api_versions = []

    def __init__(self, session, connection=None):
        super(Resource, self).__init__()
        self._session = session
        self._connection = connection
        self._data = {}

        if self._connection is None:
            klass = self._session.get_service(self._details.service_name)
            self._connection = klass()

        self._update_docstrings()

    def __str__(self):
        return u'<{0}>'.format(
            self.__class__.__name__
        )

    def __getattr__(self, name):
        # Python didn't find it hanging off the class already, so it might
        # be instance data. Try to find it in ``_data``.
        if name in self._data:
            return self._data[name]

        raise AttributeError(
            "'{0}' object has no attribute '{1}'".format(
                self.__class__.__name__,
                name
            )
        )

    def __setattr__(self, name, value):
        # Check to see if it's a value for a known field first.
        if name in self.fields:
            self._data[name] = value
            return

        # Must be regular assignment.
        super(Resource, self).__setattr__(name, value)

    def _update_docstrings(self):
        # Because this is going to get old typing & re-typing.
        cls = self.__class__

        for attr_name, method in cls._instance_methods.items():
            method.update_docstring(self)
