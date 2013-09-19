from boto3.utils import OrderedDict
from boto3.utils import six


class StructureMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name in ['NewBase', 'Resource']:
            # Grumble grumble six grumble.
            return super(StructureMetaclass, cls).__new__(
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
        }

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

        klass = super(StructureMetaclass, cls).__new__(cls, name, bases, attrs)
        return klass


class Structure(six.with_metaclass(StructureMetaclass)):
    # Subclasses should always specify this & list out the API versions
    # it supports.
    valid_api_versions = []

    def __init__(self):
        super(Structure, self).__init__()
        self._data = {}

    def __str__(self):
        return u'<{0}: {1}>'.format(
            self.__class__.__name__,
            self._data
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
        super(Structure, self).__setattr__(name, value)
