import six

from boto3.core.constants import DEFAULT_REGION
from boto3.core.constants import NOTHING_PROVIDED
from boto3.core.introspection import Introspection


class ServiceDetails(object):
    service_name = 'unknown'
    session = None

    def __init__(self, service_name, session):
        super(ServiceDetails, self).__init__()
        self.service_name = service_name
        self.session = session
        self._api_version = None
        self._loaded_service_data = None

    def __str__(self):
        return u'<{0}: {1} - {2}>'.format(
            self.__class__.__name__,
            self.service_name,
            self.api_version
        )

    @property
    def service_data(self):
        # Lean on the cache first.
        if self._loaded_service_data is not None:
            return self._loaded_service_data

        # We don't have a cache. Build it.
        self._loaded_service_data = self._introspect_service(
            # We care about the ``botocore.session`` here, not the
            # ``boto3.session``.
            self.session.core_session,
            self.service_name
        )
        # Clear out the API version, just in case.
        self._api_version = None
        return self._loaded_service_data

    @property
    def api_version(self):
        # Lean on the cache first.
        if self._api_version is not None:
            return self._api_version

        # We don't have a cache. Build it.
        self._api_version = self._introspect_api_version(
            self.session.core_session,
            self.service_name
        )
        return self._api_version

    def _introspect_service(self, core_session, service_name):
        # Yes, we could lean on ``self.session|.service_name`` here,
        # but this makes testing/composability easier.
        intro = Introspection(core_session)
        return intro.introspect_service(service_name)

    def _introspect_api_version(self, core_session, service_name):
        intro = Introspection(core_session)
        service = intro.get_service(service_name)
        return service.api_version

    def reload_service_data(self):
        self._loaded_service_data = None
        return self.service_data


class Connection(object):
    """
    A common base class for all the ``Connection`` objects.
    """
    def __init__(self, region_name=DEFAULT_REGION):
        super(Connection, self).__init__()
        self.region_name = region_name

    def __str__(self):
        return u'<{0}: {0}>'.format(
            self.__class__.__name__,
            self.region_name
        )

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

    @classmethod
    def connect_to_region(cls, **kwargs):
        return cls(**kwargs)

    def _get_operation_data(self, method_name):
        """
        Returns all the introspected operation data for a given method.
        """
        return self._details.service_data[method_name]

    # TODO: Implement further convenience methods for accessing param info
    #       & whatnot. (For the Resource layer to use.)

    def _get_operation_params(self, method_name):
        return self._get_operation_data(method_name).get('params', [])


class ServiceFactory(object):
    def __init__(self, session, base_service=Connection,
                 details_class=ServiceDetails):
        super(ServiceFactory, self).__init__()
        self.session = session
        self.base_service = base_service
        self.details_class = ServiceDetails

    def __str__(self):
        return self.__class__.__name__

    def construct_for(self, service_name):
        # Construct a new ``ServiceDetails`` (or similar class) for storing
        # the relevant details about the service & its operations.
        details = self.details_class(service_name, self.session)
        # Make sure the new class gets that ``ServiceDetails`` instance as a
        # ``cls._details`` attribute.
        attrs = {
            '_details': details,
        }

        # Determine what we should call it.
        klass_name = self._build_class_name(service_name)

        # Construct what the class ought to have on it.
        attrs.update(self._build_methods(details))

        # Create the class.
        return type(
            klass_name,
            (Connection,),
            attrs
        )

    def _build_class_name(self, service_name):
        return '{0}Connection'.format(service_name.capitalize())

    def _build_methods(self, details):
        attrs = {}

        for method_name, op_data in details.service_data.items():
            # First we make expand then we defense it.
            # Construct a brand-new method & assign it on the class.
            attrs[method_name] = self._create_operation_method(method_name, op_data)

        return attrs

    def _create_operation_method(factory_self, method_name, orig_op_data):
        if not six.PY3:
            method_name = str(method_name)

        def _new_method(self, **kwargs):
            # Fetch the information about the operation.
            op_data = self._get_operation_data(method_name)

            # Check the parameters.
            self._check_method_params(
                op_data['params'],
                **kwargs
            )

            # Prep the service's parameters.
            service_params = self._build_service_params(
                op_data['params'],
                **kwargs
            )

            # Actually call the service.
            service = self._details.session.get_core_service(
                self._details.service_name
            )
            endpoint = service.get_endpoint(self.region_name)
            op = service.get_operation(
                op_data['api_name']
            )
            results = op.call(endpoint, **service_params)

            # Post-process results here
            post_processed = self._post_process_results(
                method_name,
                op_data['output'],
                results
            )
            return post_processed

        # Swap the name, so it looks right.
        _new_method.__name__ = method_name
        # Assign docstring.
        _new_method.__doc__ = orig_op_data['docs']
        # Return the newly constructed method.
        return _new_method
