import six


class ResourceCollectionMetaclass(type):
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
            'collection': orig_attrs.pop('collection', None),
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
                if getattr(value, 'is_instance_method', False):
                    attrs['_instance_methods'][attr_name] = value
                    setattr(value, 'name', attr_name)

        klass = super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)

        # Once we're done constructing the base object, go back & add on the
        # methods.
        # We do this after the fact so that we can let the ``Resource`` (or
        # similar) class handle the construction of the methods.
        # This avoids further metaclass hackery & puts the subclass in control,
        # rather than embedding that logic here.
        for attr_name, method in klass._instance_methods.items():
            method.setup_on_resource(klass)

        return klass


@six.add_metaclass(ResourceCollectionMetaclass)
class ResourceCollection(object):
    # Subclasses should always specify this & list out the API versions
    # it supports.
    valid_api_versions = []
