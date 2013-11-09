import os

from boto3.core.constants import DEFAULT_RESOURCE_JSON_DIR
from boto3.core.exceptions import NoResourceJSONFound
from boto3.utils import json


class ResourceJSONLoader(object):
    default_data_dirs = [
        DEFAULT_RESOURCE_JSON_DIR,
    ]

    def __init__(self, data_dirs=None):
        self.data_dirs = data_dirs
        self._loaded_data = {}

        if self.data_dirs is None:
            self.data_dirs = self.default_data_dirs

    def construct_filepath(self, path, service_name):
        return os.path.join(path, "{0}.json".format(service_name))

    def load(self, service_name):
        data = {}

        # Check the various paths for overridden versions. Take the first one
        # we find.
        for data_path in self.data_dirs:
            file_path = self.construct_filepath(data_path, service_name)

            if not os.path.exists(file_path):
                continue

            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                # Embed where we found it from for debugging purposes.
                data['__file__'] = file_path

        if not data:
            msg = "No JSON for '{0}' could be found on paths:\n".format(
                service_name
            )
            msg += '\n'.join([' - {0}'.format(path) for path in self.data_dirs])
            raise NoResourceJSONFound(msg)

        return data

    def __getitem__(self, service_name):
        # Fetch from the cache first if it's there.
        if service_name in self._loaded_data:
            return self._loaded_data[service_name]

        # Set it within the cache.
        self._loaded_data[service_name] = self.load(service_name)
        return self._loaded_data[service_name]

    def __contains__(self, service_name):
        return service_name in self._loaded_data


# Default instance for convenience.
default_loader = ResourceJSONLoader()
