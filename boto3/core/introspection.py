from boto3.core.constants import DEFAULT_REGION
from boto3.utils.mangle import html_to_rst


class Introspection(object):
    """
    Used to introspect ``botocore`` objects (``Service``, ``Operation`` &
    ``Endpoint``) to determine what operations/parameters/etc. are available.

    Done here to encapsulate the data needed from ``botocore``, to limit
    API changes elsewhere in ``boto`` should ``botocore`` change.

    Usage::

        >>> from botocore.session import Session
        >>> session = Session()
        >>> intro = Introspection(session)
        >>> intro.introspect_service('s3')
        {
            # ...big bag of operation data...
        }

    """
    def __init__(self, session):
        """
        Creates a new ``Introspection`` instance.

        :param session: A ``botocore`` session to introspect with.
        :type session: A ``<botocore.session.Session>`` instance
        """
        super(Introspection, self).__init__()
        # TODO: For now, this is a ``botocore.session.Session``. We may want
        #       to use a ``boto3.core.session.Session`` instead?
        self.session = session

    def get_service(self, service_name):
        """
        Returns a ``botocore.service.Service`` object for a given service.

        :param service_name: The desired service name
        :type service_name: string

        :returns: A <botocore.service.Service> object
        """
        return self.session.get_service(service_name)

    def get_endpoint(self, service, region_name=DEFAULT_REGION):
        """
        Returns a ``botocore.endpoint.Endpoint`` object for a given service.

        :param service: A ``Service`` object
        :type service: A ``<botocore.service.Service>`` instance

        :param region_name: (Optional) The name of the region you'd like to
            connect to. By default, this is
            ``boto3.core.constants.DEFAULT_REGION``.
        :type region_name: string

        :returns: A <botocore.endpoint.Endpoint> object
        """
        return service.get_endpoint(region_name=region_name)

    def get_operation(self, service, operation_name):
        """
        Returns a ``botocore.operation.Operation`` object for a given service
        & operation name.

        :param service_name: The desired service name
        :type service_name: string

        :param operation_name: The API name of the operation you'd like to
            execute. Ex. ``PutBucketCORS``
        :type operation_name: string

        :returns: A <botocore.operation.Operation> object
        """
        return service.get_operation(operation_name)

    def parse_param(self, core_param):
        """
        Returns data about a specific parameter.

        :param core_param: The ``Parameter`` to introspect
        :type core_param: A ``<botocore.parameters.Parameter>`` subclass

        :returns: A dict of the relevant information
        """
        return {
            'var_name': core_param.py_name,
            'api_name': core_param.name,
            'required': core_param.required,
            'type': core_param.type,
        }

    def parse_params(self, core_params):
        """
        Goes through a set of parameters, extracting information about each.

        :param core_params: The collection of parameters
        :type core_params: A collection of ``<botocore.parameters.Parameter>``
            subclasses

        :returns: A list of dictionaries
        """
        params = []

        for core_param in core_params:
            params.append(self.parse_param(core_param))

        return params

    def introspect_operation(self, operation):
        """
        Introspects an entire operation, returning::

        * the method name (to expose to the user)
        * the API name (used server-side)
        * docs
        * introspected information about the parameters
        * information about the output

        :param operation: The operation to introspect
        :type operation: A <botocore.operation.Operation> object

        :returns: A dict of information
        """
        return {
            'method_name': operation.py_name,
            'api_name': operation.name,
            'docs': html_to_rst(operation.documentation),
            'params': self.parse_params(operation.params),
            'output': operation.output,
        }

    def introspect_service(self, service_name):
        """
        Introspects all the operations (& related information) about a service.

        :param service_name: The desired service name
        :type service_name: string

        :returns: A dict of all operation names & information
        """
        data = {}
        service = self.get_service(service_name)

        for operation in service.operations:
            # These are ``Operation`` objects, not operation strings.
            op_data = self.introspect_operation(operation)
            data[op_data['method_name']] = op_data

        return data
