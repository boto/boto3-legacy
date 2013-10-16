from boto3.core.constants import DEFAULT_DOCSTRING
from boto3.core.constants import NO_NAME
from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.constants import NO_RESOURCE
from boto3.core.exceptions import NoNameProvidedError
from boto3.core.exceptions import NoResourceAttachedError
from boto3.utils.mangle import to_snake_case


class BaseMethod(object):
    name = NO_NAME
    is_method = True

    def __init__(self, conn_method_name=None, **kwargs):
        super(BaseMethod, self).__init__()
        self.conn_method_name = conn_method_name
        self.resource = NO_RESOURCE
        self._partial = kwargs

    def check_name(self):
        if self.name == NO_NAME:
            raise NoNameProvidedError(
                "'{0}' hasn't been given a name on '{1}'.".format(
                    self.__class__.name,
                    self.resource
                )
            )

    def check_resource_class(self):
        if self.resource == NO_RESOURCE:
            err = "'{0}' hasn't been attached to a 'Resource' class. " + \
                  "You probably need to call '{1}.setup_on_resource(...)' " + \
                  "if you've dynamically added this field."
            raise NoResourceAttachedError(
                err.format(
                    self.name,
                    self.__class__.name
                )
            )

    def setup_on_resource(self, resource_class):
        raise NotImplementedError(
            "Subclasses must override this method & correctly attach to " + \
            "the Resource class."
        )

    def teardown_on_resource(self, resource_class):
        delattr(resource_class, self.name)

    def get_expected_parameters(self, conn):
        return conn._get_operation_params(self.conn_method_name)

    def get_bound_params(self, expected_params):
        # TODO: This is pretty naive for now.
        #       Just return all the values we see from expected that might be
        #       hanging off the class.
        bound_params = {}

        # FIXME: The nested for loop is slow/bad. We should map out the data
        #        once (``{api_name: _data[name]}``) to limit this.
        for param_info in expected_params:
            for name, value in self.resource.fields.items():
                if value.snake_name == param_info['var_name']:
                    bound_params[value.snake_name] = getattr(
                        self.resource,
                        name,
                        NOTHING_PROVIDED
                    )

        return bound_params

    def check_required_params(self, expected_params, built_params):
        # TODO: The underlying ``Connection`` will also check params, so we
        #       really only need to do higher-level checking here, if at all?
        pass

    def update_bound_params_from_api(self, raw_results):
        for key, value in raw_results.items():
            # Ouch.
            # botocore only snake_case's the variables one-way (as
            # params, not in return values), so we have to lean on the
            # API names here. :(
            for name, field in self.resource.fields.items():
                if field.api_name == key:
                    setattr(
                        self.resource,
                        name,
                        value,
                    )

    def post_process_results(self, raw_results):
        # TODO: For now, we're just passing through the results.
        #       Again, this is pretty leaky as far as I'm concerned, but I'm
        #       not sure how to generically mitigate this for the moment.
        return raw_results

    def call(self, conn, **kwargs):
        # Start by partially applying whatever kwargs it was instantiated with.
        # Because reasonable defaults.
        built_params = self._partial
        # Then update it with what was passed in (allowing overrides).
        # TODO: Perhaps this should happen after the bound params?
        built_params.update(kwargs)

        # Determine the parameters this method should accept.
        expected_params = self.get_expected_parameters(conn)

        # Next, update **kwargs with bound/instance variables.
        if hasattr(self.resource, 'fields'):
            built_params.update(self.get_bound_params(expected_params))

        # Now that we have all the data, check to make sure we've got all the
        # required parameters.
        self.check_required_params(expected_params, built_params)

        # Call the connection method & get the results.
        conn_method = getattr(conn, self.conn_method_name)
        raw_results = conn_method(**built_params)

        # Check the output for bound data & update the instance.
        if hasattr(self.resource, 'fields'):
            self.update_bound_params_from_api(raw_results)

        # Return whatever is left.
        results = self.post_process_results(raw_results)
        return results

    def update_docstring(self, resource):
        # FIXME: Just blindly copies the docstring from the low-level, which
        #        isn't particularly good.
        #        Templates, parsing & better params (since we can know them)
        #        would be best.
        if self.resource == NO_RESOURCE:
            self.resource = resource

        method = getattr(resource.__class__, self.name)
        conn_method = getattr(resource._connection, self.conn_method_name)
        method.__doc__ = conn_method.__doc__


class InstanceMethod(BaseMethod):
    is_instance_method = True

    def setup_on_resource(meth_self, resource_class):
        def _new_method(self, **kwargs):
            meth_self.resource = self
            # FIXME: This needs to update the resource's instance data.
            return self._methods[meth_self.name].call(
                self._connection,
                **kwargs
            )

        # Set the name/docs & hook it up to the class.
        _new_method.__name__ = meth_self.name
        _new_method.__doc__ = DEFAULT_DOCSTRING
        setattr(resource_class, meth_self.name, _new_method)
        return True


class CollectionMethod(BaseMethod):
    is_collection_method = True

    def setup_on_resource(meth_self, resource_class):
        def _new_method(self, **kwargs):
            meth_self.resource = self
            # FIXME: This needs to:
            #        1. Expect a list of resources
            #        2. Build those **OBJECTS** & return them, not just blindly
            #           returning data
            return self._methods[meth_self.name].call(
                self._connection,
                **kwargs
            )

        # Set the name/docs & hook it up to the class.
        _new_method.__name__ = meth_self.name
        _new_method.__doc__ = DEFAULT_DOCSTRING
        setattr(resource_class, meth_self.name, _new_method)
        return True
