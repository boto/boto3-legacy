from boto3.core.constants import DEFAULT_REGION
from boto3.utils.mangle import to_snake_case
from boto3.utils.mangle import to_camel_case
from boto3.utils.mangle import html_to_rst


class Introspection(object):
    def __init__(self, session):
        super(Introspection, self).__init__()
        # TODO: For now, this is a ``botocore.session.Session``. We may want
        #       to use a ``boto3.core.session.Session`` instead?
        self.session = session

    def get_service(self, service_name):
        return self.session.get_service(service_name)

    def get_endpoint(self, service, region_name=DEFAULT_REGION):
        return service.get_endpoint(region_name=region_name)

    def get_operation(self, service, operation_name):
        return service.get_operation(operation_name)

    def parse_param(self, core_param):
        return {
            'var_name': to_snake_case(core_param.name),
            'api_name': core_param.name,
            'required': core_param.required,
            'type': core_param.type,
        }

    def parse_params(self, core_params):
        params = []

        for core_param in core_params:
            params.append(self.parse_param(core_param))

        return params

    def introspect_operation(self, operation):
        return {
            'method_name': to_snake_case(operation.name),
            'api_name': operation.name,
            'docs': html_to_rst(operation.documentation),
            'params': self.parse_params(operation.params),
            'output': operation.output,
        }

    def introspect_service(self, service_name):
        data = {}
        service = self.get_service(service_name)

        for operation in service.operations:
            # These are ``Operation`` objects, not operation strings.
            op_data = self.introspect_operation(operation)
            data[op_data['method_name']] = op_data

        return data
