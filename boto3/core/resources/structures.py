from boto3.core.exceptions import UnknownFieldError
from boto3.utils import OrderedDict
from boto3.utils import six


class StructureMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # Check if we're dealing with the base class.
        # If so, don't run the rest of the metaclass.
        if name in ['Structure']:
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
            'possible_paths': orig_attrs.pop('possible_paths', []),
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
            else:
                attrs[attr_name] = value

        klass = super(StructureMetaclass, cls).__new__(cls, name, bases, attrs)
        return klass


@six.add_metaclass(StructureMetaclass)
class Structure(object):
    # Subclasses should always specify this & list out the API versions
    # it supports.
    valid_api_versions = []
    possible_paths = []

    def __init__(self, **kwargs):
        super(Structure, self).__init__()
        self._data = {}

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return u'<{0}: {1}>'.format(
            self.__class__.__name__,
            self._data
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
        super(Structure, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in self.fields:
            self.fields[name].delete(self)
            return

        # Must be regular deletion.
        super(Structure, self).__delattr__(name)

    def full_populate(self, data):
        """
        Fires when receiving data from the service.

        Useful for verification & type conversion.

        For the end user, you'll typically define a ``post_populate()`` method
        that further works with the data.
        """
        for key, raw_value in data.items():
            for name, field in self.fields.items():
                if field.api_name == key:
                    # Allow the field to control the population of the value.
                    self.fields[field.name].set_python(self, raw_value)
                    break

        if hasattr(self, 'post_populate'):
            self.post_populate(data)

    def full_prepare(self):
        """
        Fires when data is about to be sent to the service.

        For the end user, you'll typically define a ``prepare()`` method
        that further works with the data.
        """
        data = {}

        for fieldname in self.fields.keys():
            field = self.fields[fieldname]

            try:
                data[fieldname] = field.get_api(self)
            except KeyError as err:
                if field.required is False:
                    continue

                # TODO: Consider a different exception here, since a
                #       ``KeyError`` may not make much sense to the end user.
                raise

        if hasattr(self, 'prepare'):
            data = self.prepare(data)

        return data

