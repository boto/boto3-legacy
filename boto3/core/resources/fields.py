from boto3.utils.mangle import to_snake_case


class BaseField(object):
    name = 'unknown'
    is_field = True

    def __init__(self, api_name, name=None, required=True):
        super(BaseField, self).__init__()
        self.api_name = api_name
        # An optimization for dealing with botocore.
        # See ``boto3.core.resources.methods.BaseMethod.update_bound_params_from_api``
        # for details...
        self.snake_name = to_snake_case(api_name)
        self.required = required

        if name:
            self.name = name

    def get_python(self, instance):
        return instance._data[self.name]

    def set_python(self, instance, value):
        instance._data[self.name] = value

    def get_api(self, instance):
        return instance._data[self.name]

    def set_api(self, instance, value):
        instance._data[self.name] = value

    def delete(self, instance):
        # TODO: This is mostly just a hook & likely an unnecessary one.
        #       For now, we'll leave it & use it, but we should re-evaluate
        #       it before we launch.
        del instance._data[self.name]


class BoundField(BaseField):
    pass


class ListBoundField(BaseField):
    is_collection = True

    # FIXME: Needs further customizations for lists.
    def __init__(self, api_name, data_class, **kwargs):
        self.data_class = data_class
        super(ListBoundField, self).__init__(api_name, **kwargs)

    def get_api(self, instance):
        raw_data = instance._data[self.name]
        data = []

        for item in raw_data:
            if hasattr(item, 'full_prepare'):
                data.append(item.full_prepare())
            else:
                data.append(item)

        return data
