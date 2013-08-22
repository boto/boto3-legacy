import six
import weakref

from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.introspection import Introspection


class ServiceDetails(object):
    service_name = 'unknown'
    session = None

    def __init__(self, service_name, session):
        super(ServiceDetails, self).__init__()
        self.service_name = service_name
        # Use a weakref, so that GC isn't held up.
        self.session = weakref.ref(session)


class Connection(object):
    """
    A common base class for all the ``Connection`` objects.
    """
    def __init__(self, region_name='us-east-1'):
        super(Connection, self).__init__()
        self.region_name = region_name

    @classmethod
    def connect_to_region(cls, **kwargs):
        return cls(**kwargs)


class ServiceMethod(object):
    def __init__(self, service_name, method_name, op_data):
        super(ServiceMethod, self).__init__()
        self.service_name = service_name
        self.method_name = method_name
        self.op_data = op_data

    @classmethod
    def construct_from_op_data(cls, service_name, method_name, op_data):
        method = cls(
            service_name=service_name,
            method_name=method_name,
            op_data=op_data
        )

        # Swap the name, so it looks right.
        method.__name__ = method_name
        # Assign docstring.
        method.__doc__ = op_data['docs']
        return method

    def _check_method_params(self, op_params, **kwargs):
        # For now, we don't type-check or anything, just check for required
        # params.
        for param in op_params:
            if param['required'] is True:
                if not param['var_name'] in kwargs:
                    err = "Missing required parameter: '{0}'".format(
                        param['var_name']
                    )
                    raise TypeError(err)

    def _build_service_params(self, op_params, **kwargs):
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

    def _post_process_results(self, method_name, output, results):
        # TODO: Maybe build in an extension mechanism (like
        #      ``post_process_<op_name>_results``)?
        return results[1]

    def __call__(self, **kwargs):
        # Check the parameters.
        self._check_method_params(self.op_data['params'], **kwargs)

        # Prep the service's parameters.
        service_params = self._build_service_params(
            self.op_data['params'],
            **kwargs
        )

        # Actually call the service.
        service = self._details.session.get_core_service(
            self._details.service_name
        )
        endpoint = service.get_endpoint(self.region_name)
        op = service.get_operation(self.op_data['api_name'])
        results = op.call(endpoint, **service_params)

        # Post-process results here
        post_processed = self._post_process_results(
            method_name,
            self.op_data['output'],
            results
        )
        return post_processed


class ServiceFactory(object):
    def __init__(self, session, base_service=Connection):
        super(ServiceFactory, self).__init__()
        self.session = session
        self.base_service = base_service

    def construct_for(self, service_name):
        attrs = {
            '_details': ServiceDetails(service_name, self.session),
        }

        # Determine what we should call it.
        klass_name = self._build_class_name(service_name)

        # Construct what the class ought to have on it.
        attrs.update(self._build_methods(service_name))

        # Create the class.
        return type(
            klass_name,
            (Connection,),
            attrs
        )

    def _build_class_name(self, service_name):
        return '{0}Connection'.format(service_name.capitalize())

    def _build_methods(self, service_name):
        service_data = self._introspect_service(
            # We care about the ``botocore.session`` here, not the
            # ``boto3.session``.
            self.session.core_session,
            service_name
        )
        attrs = {}

        for method_name, op_data in service_data.items():
            # First we make expand then we defense it.
            # Construct a brand-new method & assign it on the class.
            attrs[method_name] = self._create_operation_method(service_name, method_name, op_data)

        return attrs

    def _introspect_service(self, core_session, service_name):
        # Yes, we could lean on ``self.session|.service_name`` here,
        # but this makes testing/composability easier.
        intro = Introspection(core_session)
        return intro.introspect_service(service_name)

    def _create_operation_method(self, method_name, op_data):
        if not six.PY3:
            method_name = str(method_name)

        _new_method = ServiceMethod.construct_from_op_data(
            method_name,
            op_data
        )
        # Return the newly constructed "method".
        return _new_method
