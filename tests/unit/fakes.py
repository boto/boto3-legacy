class FakeParam(object):
    def __init__(self, name, required=False, ptype='string'):
        self.name = name
        self.required = required
        self.type = ptype


class FakeOperation(object):
    def __init__(self, name, docs='', params=None, output=None):
        self.name = name
        self.documentation = docs
        self.params = params
        self.output = output

        if self.params is None:
            self.params = []

        if self.params is None:
            self.params = {}


class FakeService(object):
    operations = []

    def __init__(self):
        pass


class FakeSession(object):
    def __init__(self, service):
        self.service = service

    def get_service(self, service_name):
        return self.service
