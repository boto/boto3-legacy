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

    def __init__(self, conn_method_name=None):
        super(BaseMethod, self).__init__()
        self.conn_method_name = conn_method_name
        self.resource = NO_RESOURCE

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
                if value.api_name == param_info['var_name']:
                    bound_params[value.api_name] = getattr(
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
            # FIXME: Ouch.
            #        botocore only snake_case's the variables one-way (as
            #        params, not in return values), so we have to do a little
            #        hocus-pocus guessing about names. :(
            # FIXME: Alternatively, we could snake_case in the field's
            #        ``__init``, which would allow us to use the regular API
            #        name here (we'd have to use the alternate snake'd version
            #        above in ``get_bound_params``).
            snaked_key = to_snake_case(key)

            for name, field in self.resource.fields.items():
                if field.api_name == snaked_key:
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

    # TODO: If these stay as plain class/instance-attributes (Option #1), this
    #       needs to become ``__call__`` instead of ``call``.
    def call(self, conn, **kwargs):
        built_params = kwargs

        # Determine the parameters this method should accept.
        expected_params = self.get_expected_parameters(conn)

        # Next, update **kwargs with bound/instance variables.
        built_params.update(self.get_bound_params(expected_params))

        # Now that we have all the data, check to make sure we've got all the
        # required parameters.
        self.check_required_params(expected_params, built_params)

        # Call the connection method & get the results.
        conn_method = getattr(conn, self.conn_method_name)
        raw_results = conn_method(**built_params)

        # Check the output for bound data & update the instance.
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
            return self._instance_methods[meth_self.name].call(
                self._connection,
                **kwargs
            )

        # Set the name/docs & hook it up to the class.
        _new_method.__name__ = meth_self.name
        _new_method.__doc__ = DEFAULT_DOCSTRING
        setattr(resource_class, meth_self.name, _new_method)
        return True


class ClassMethod(BaseMethod):
    is_class_method = True

    def setup_on_resource(meth_self, resource_class):
        def _new_method(cls, **kwargs):
            meth_self.resource = cls
            return cls._class_methods[meth_self.name].call(
                # FIXME: No clue how a connection will get here. That's a bit
                #        of a deal-breaker for class methods. :(
                **kwargs
            )

        # Set the name/docs & hook it up to the class.
        _new_method.__name__ = meth_self.name
        _new_method.__doc__ = DEFAULT_DOCSTRING
        setattr(resource_class, meth_self.name, classmethod(_new_method))
        return True
