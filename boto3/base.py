from boto3.constants import NOTHING_PROVIDED, NOTHING_RECEIVED
from boto3.exceptions import NoSuchObject


class BotoObject(object):
    service_name = 'UnknownService'
    _json_name = 'Unknown'
    _json = {}
    _loaded = False

    def __init__(self, session, lazy=False):
        self.session = session
        # FIXME: This may need to be altered to be lazier.
        self.client = session.get_client(self.service_name)

        if not lazy:
            self._construct_object()

    @classmethod
    def _reset(cls):
        cls._json = {}
        cls._loaded = False

    def _get_objects_json(self):
        return list(self.__class__._json.keys())

    def _get_mappings_json(self):
        return self.__class__._json.get(self._json_name).get('mappings', {})

    def _get_json(self):
        return self.session.load_json_for(self.service_name)

    def _construct_object(self):
        klass = self.__class__

        if klass._loaded:
            return True

        klass._json = self._get_json()
        objects = self._get_objects_json()
        mappings = self._get_mappings_json()

        if not self._json_name in objects:
            err = "Service '{0}' has no object named '{1}'."
            raise NoSuchObject(err.format(self.service_name, self._json_name))

        self._add_methods(mappings)
        klass._loaded = True
        return True

    def _get_endpoint(self):
        # FIXME: This is hardcoded & can't stay.
        return self.client.get_endpoint('us-west-2')

    def _get_operation(self, op_name):
        return self.client.get_operation(op_name)

    def _check_required(self, mapping, kwargs):
        # TODO: Caching this list might be beneficial for performance.
        for param, param_info in mapping['parameters'].items():
            if param_info.get('required', False):
                if not param in kwargs:
                    err = "Missing required parameter '{0}'."
                    raise AttributeError(err.format(param))

        return True

    def _build_client_parameters(self, mapping, kwargs):
        data_to_send = {}

        for actual_name, meta in mapping['client_parameters'].items():
            source_from = meta.get('source_from', 'parameter')
            required = meta.get('required', False)
            variable = meta['variable']

            if source_from == 'instance':
                value = getattr(self, variable, NOTHING_PROVIDED)
            elif source_from == 'parameter':
                value = kwargs.get(variable, NOTHING_PROVIDED)

            if value is NOTHING_PROVIDED:
                # If it's not provided & not required, we don't care.
                if required:
                    err = "No value provided required parameter '{0}'."
                    raise AttributeError(err.format(variable))
            else:
                data_to_send[actual_name] = value

        return data_to_send

    def _handle_result(self, mapping, result):
        ret_vals = {}

        for key, meta in mapping['result'].items():
            behavior = meta.get('behavior', 'store_instance')
            data = result[1]
            value = NOTHING_RECEIVED

            if '.' in key:
                # It's a path-alike.
                # FIXME: Ignore for now, but this needs a recursive lookup
                #        eventually.
                pass
            else:
                value = data.get(key, NOTHING_RECEIVED)

            if value is NOTHING_RECEIVED:
                # FIXME: Maybe this is an error?
                continue

            if behavior == 'store_instance':
                store_as = meta['store_as']
                setattr(self, store_as, value)
            elif behavior == 'return_value':
                return_key = meta['return_key']
                ret_vals[return_key] = value
            else:
                err = "Hey! Implement me for {0}!"
                raise NotImplementedError(err.format(behavior))

        return ret_vals

    @staticmethod
    def _create_method(name, mapping):
        def _method(self, *args, **kwargs):
            mapping = self._get_mappings_json()

            # Check the supplied parameters for missing data.
            self._check_required(kwargs, mapping)
            # Build the arguments we're going to send down to the client.
            data_to_send = self._build_client_parameters(mapping, kwargs)

            endpoint = self._get_endpoint()
            operation = self._get_operation(mapping['client_method'])
            # FIXME: This is in sore need of some error handling.
            result = operation.call(endpoint, **data_to_send)

            # Update any instance data & get return values.
            ret_vals = self._handle_result(mapping, result)
            return ret_vals

        _method.__name__ = name
        return _method

    def _add_methods(self, mappings=None):
        klass = self.__class__

        if mappings is None:
            mappings = {}

        for method_name, mapping in mappings.get(self._json_name, {}).items():
            klass.method = klass._create_method(method_name, mapping)

        return True
