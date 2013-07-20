import six

from boto3.core.exceptions import NoSuchMethod


class ResourceDetails(object):
    def __init__(self):
        super(ResourceDetails, self).__init__()
        self.connection_class = None
        self.instance_vars = {}
        self.crud = {}
        self.depends_on = {}
        self.reflected_vars = {}


class ResourceMetaclass(type):
    def __new__(cls, name, bases, attrs):
        details = ResourceDetails()
        details.connection_class = attrs.pop('connection_class')
        details.instance_vars = attrs.pop('instance_vars', {})
        details.crud = attrs.pop('crud', {})
        details.depends_on = attrs.pop('depends_on', {})

        # Reflect the ``instance_vars`` for speed, so setting data based on
        # a retun value is fast.
        # Can't use a dictionary comprehension because of Py2.6. :(
        for key, value in details.instance_vars.items():
            details.reflected_vars[value] = key

        attrs['_details'] = details
        klass = super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)
        return klass


class Resource(six.with_metaclass(ResourceMetaclass)):
    def _get_connection(self):
        # FIXME: This needs to take into account region information.
        # FIXME: This is also ripe for memoization.
        return self._details.connection_class()

    def _determine_method_name(self, orig_name):
        method_name = self._details.crud.get(orig_name)

        if not method_name:
            err = "{0} doesn't implement the '{1}' method.".format(
                self.__class__.__name__,
                method_name
            )
            raise NotImplementedError(err)

        return method_name

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
