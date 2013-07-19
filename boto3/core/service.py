import botocore.session

from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.introspection import Introspection


class ServiceDetails(object):
    service_name = 'unknown'
    default_session = None

    def __str__(self):
        return 'ServiceDetails: {0}'.format(self.service_name)


class ServiceMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if not 'service_name' in attrs:
            # Because ``six`` lies to us. Bail out if it's not an actual
            # ``Service``-like class.
            return super(ServiceMetaclass, cls).__new__(
                cls, name, bases, attrs
            )

        details = ServiceDetails()
        details.service_name = attrs.pop('service_name')
        attrs['_details'] = details

        # Create the class.
        klass = super(ServiceMetaclass, cls).__new__(cls, name, bases, attrs)

        # We're not done yet. Assign the session first.
        details.session = klass._get_session()

        # Construct what the class ought to have on it.
        klass._build_methods()
        return klass


class Service(object):
    # All ``Service`` objects must add a ``service_name`` class variable, which
    # should be the name of the service.
    # service_name = '...'

    @classmethod
    def _get_session(cls):
        # FIXME: This is a **HUGE** unanswered question. How, at import time,
        #        can we supply the correct ``Session`` object? :/
        #        For now, hack it & move on.
        return botocore.session.get_session()

    @classmethod
    def _build_methods(cls):
        # The big, nasty integration method that stitches this all together.
        # For sanity (& testing), this should be the only method that changes
        # class-state.
        service_data = cls._introspect_service(
            cls._details.session,
            cls._details.service_name
        )

        for method_name, op_data in service_data.items():
            # First we make expand then we defense it.
            # Construct a brand-new method & assign it on the class.
            setattr(
                cls,
                method_name,
                cls._create_operation_method(method_name, op_data)
            )

    @classmethod
    def _introspect_service(cls, session, service_name):
        # Yes, we could lean on ``cls._details.session|.service_name`` here,
        # but this makes testing/composability easier.
        intro = Introspection(session)
        return intro.introspect_service(service_name)

    @classmethod
    def _create_operation_method(cls, method_name, op_data):
        def _new_method(self, **kwargs):
            klass = self.__class__

            # Check the parameters.
            klass._check_method_params(op_data['params'], **kwargs)

            # Prep the service's parameters.
            service_params = klass._build_service_params(
                op_data['params'],
                **kwargs
            )

            # Actually call the service.
            service = self._details.session.get_service(
                self._details.service_name
            )
            # FIXME: This can't stay hard-coded & needs changing.
            endpoint = service.get_endpoint('us-east-1')
            op = service.get_operation(op_data['api_name'])
            results = op.call(endpoint, **service_params)

            # Post-process results here
            post_processed = klass._post_process_results(
                method_name,
                op_data['output'],
                results
            )
            return post_processed

        # Swap the name, so it looks right.
        _new_method.__name__ = method_name
        # Assign docstring.
        _new_method.__doc__ = op_data['docs']
        # Return the newly constructed method.
        return _new_method

    @classmethod
    def _check_method_params(cls, op_params, **kwargs):
        # For now, we don't type-check or anything, just check for required
        # params.
        for param in op_params:
            if param['required'] is True:
                if not param['var_name'] in kwargs:
                    err = "Missing required parameter: '{0}'".format(
                        param['var_name']
                    )
                    raise TypeError(err)

    @classmethod
    def _build_service_params(cls, op_params, **kwargs):
        # TODO: Maybe build in an extension mechanism (like
        #      ``build_<op_name>_params``)?
        service_params = {}

        for param in op_params:
            value = kwargs.get(param['var_name'], NOTHING_PROVIDED)

            if value is NOTHING_PROVIDED:
                # They didn't give us a value. We should've already checked
                # "required-ness", so just give it a pass & move on.
                continue

            # FIXME: This is weird. I was expecting this to be
            #        ``param['api_name']`` to pass to ``botocore``, but
            #        evidently it expects snake_case here?!
            service_params[param['var_name']] = value

        return service_params

    @classmethod
    def _post_process_results(cls, method_name, output, results):
        # TODO: Maybe build in an extension mechanism (like
        #      ``post_process_<op_name>_results``)?
        # FIXME: For now, just return the data we get back from ``botocore``.
        #        This is a touch leaky, but will have to do for now.
        return results[1]
