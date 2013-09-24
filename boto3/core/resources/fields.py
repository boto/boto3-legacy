class BaseField(object):
    name = 'unknown'
    is_field = True

    def __init__(self, api_name, name=None, required=True):
        super(BaseField, self).__init__()
        self.api_name = api_name
        self.required = required

        if name:
            self.name = name

    def __get__(self, instance, owner):
        return instance._data[self.name]

    def __set__(self, instance, value):
        instance._data[self.name] = value

    def __delete__(self, instance):
        del instance._data[self.name]


class BoundField(BaseField):
    pass


class ListBoundField(BaseField):
    is_collection = True

    # FIXME: Needs further customizations for lists.
    def __init__(self, api_name, data_class, **kwargs):
        self.data_class = data_class
        super(ListBoundField, self).__init__(api_name, **kwargs)
