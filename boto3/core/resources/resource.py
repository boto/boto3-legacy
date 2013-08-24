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
            # TODO: Option #2
            '_class_methods': OrderedDict(),
            '_instance_methods': OrderedDict(),
        }

        # FIXME: So, we actually have a couple options here.
        #
        # 1. We can just assign the ``InstanceMethod/ClassMethod`` objects
        #    **as is** to the object & rely on them having a ``__call__``
        #    method to run.
        #
        #        * Simplest & perhaps most obvious
        #        * This sucks for docs (e.g. broken ``help(...)``)
        #          when it was tried for the ``Service`` operation objects
        #        * Fell down for ``Service`` operation objects because they
        #          had no reference to the parent class (& the ``session``
        #          within), which would likely break here for ``_data`` as
        #          well
        #
        # 2. We can keep the objects as is, stow them on the instance (think
        #    ``self._methods``), then construct wrapper methods that delegate
        #    off to them.
        #
        #        * A bit less obvious than #1
        #        * Way better docs
        #        * Still customizable
        #        * The most code in the metaclass :/
        #
        # 3. We can just use them as configuration data & build *real* methods
        #    out of them (a la ``ServiceFactory``).
        #
        #        * They'll feel the most natural (no objects, just functions)
        #        * Very non-obvious
        #        * Potentially complex code (that'll duplicate what's already
        #          attached to the object)
        #        * Extending this seems potentially painful & **very** difficult
        #          to manage between different methods

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
            # TODO: Option #1
            # elif getattr(value, 'is_method', True):
            #     attrs[attr_name] = value
            # TODO: Option #2
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
        # We do this after the fact so that we can let the ``Resource`` (or
        # similar) class handle the construction of the methods.
        # This avoids further metaclass hackery & puts the subclass in control,
        # rather than embedding that logic here.
        # for attr_name, value in orig_attrs.items():
        #     if getattr(value, 'is_method', False):
        #         # TODO: This code reflects option #3 from above (use the
        #         # objects) as configuration data & build *real* methods.
        #         # Not sold on this approach.
        #         if getattr(value, 'is_class_method', False):
        #             setattr(klass, name, classmethod(klass._build_class_method(
        #                 attr_name,
        #                 value
        #             )))
        #         elif getattr(value, 'is_instance_method', False):
        #             setattr(klass, attr_name, klass._build_instance_method(
        #                 attr_name,
        #                 value
        #             ))
        #         else:
        #             err = "'{0}' is an unrecognized method type. (Likely " + \
        #                   "needs either 'is_class_method' or " + \
        #                   "'is_instance_method' assigned to it)"
        #             raise ResourceError(
        #                 err.format(attr_name)
        #             )

        # TODO: Option #2
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

    # TODO: This is for option #3 (see the metaclass).
    # @classmethod
    # def _build_class_method(cls, name, value):
    #     pass

    # TODO: This is for option #3 (see the metaclass).
    # @classmethod
    # def _build_instance_method(cls, name, value):
    #     pass


#############################
# FIXME: OLD CRUD CODE BEGINS
#############################
"""
    def _get_api_method(self, conn, method_name):
        try:
            return getattr(conn, method_name)
        except AttributeError:
            err = "The connection class {0} has no method named '{1}'.".format(
                conn.__class__.__name__,
                method_name
            )
            raise NoSuchMethod(err)

    def _run(self, orig_name, **kwargs):
        method_name = self._determine_method_name(_orig_name)
        conn = self._get_connection()
        method = self._get_api_method(conn, method_name)
        return method(**params)

    def _crud(self, _orig_name, **kwargs):
        # FIXME: To be honest, I'm not totally sold on this approach.
        #        Conveniences to get the underlying connection? Yes!
        #        Conveniences to run the operation? Yes!
        #        Standardization of interfaces? Yes!
        #        Full-on mapping of things? ... Not really.
        #
        #        The concern here is both power-to-weight ratio as well as the
        #        potential complexity. Writing all these DSL-like attributes don't
        #        really get us much (beyond simplifying param construction &
        #        auto-setting attributes on return values).
        #
        #        Revisit this thought process & talk with others about it.

        # Build the params from both instance state & passed kwargs.
        params = self._build_params(**kwargs)
        # Make the actual API call through the connection.
        self._run(_orig_name, **params)

        # TODO: Store the necessary data on the instance.
        # TODO: I'm not confident about return values here. This is higher-level
        #       code, so it feels like it should only return *useful*
        #       information, not everything.
        leftovers = self._store_result_data(results)
        return leftovers

    def _build_params(self, **kwargs):
        # FIXME: This is actually hard to solve, since we're not persisting
        #        the information from the introspection & we've only got
        #        ``**kwargs`` exposed to use.
        return kwargs

    def _store_result_data(self, results):
        # FIXME: This needs updating to support jmespath & object attribute
        #        lookups.
        leftovers = {}

        for ret_key, value in results[1].items():
            if ret_key in self._details.reflected_vars:
                ivar_name = self._details.reflected_vars[ret_key]
                setattr(self, ivar_name, value)
            else:
                # TODO: Again, not sold on this part. See above.
                leftovers[ret_key] = value

        return leftovers

    @classmethod
    def create(cls, **kwargs):
        instance = cls()
        return instance._crud('create', **kwargs)

    def read(self, **kwargs):
        return self._crud('read', **kwargs)

    def update(self, **kwargs):
        return self._crud('update', **kwargs)

    def delete(self, **kwargs):
        return self._crud('delete', **kwargs)
"""
