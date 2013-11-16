import os

from boto3.core.constants import DEFAULT_RESOURCE_JSON_DIR
from boto3.core.exceptions import NoResourceJSONFound
from boto3.utils import json


class ResourceJSONLoader(object):
    """
    Handles the loading of the ResourceJSON. Can be overridden to look up
    user-defined paths first, with fallbacks.

    For optimal efficiency, one loader instance should be used in as many
    places as possible & use the ``__getitem__`` (dictionary-style) lookups.
    This will populate the cache, causing subsequent lookups to be fast & one
    instance will prevent memory bloat.

    Usage::

        >>> rjl = ResourceJSONLoader()
        # Load it no matter what.
        >>> rjl.load('s3')
        {
            # ...S3's ResourceJSON as a dict...
        }
        # Get a cached version (or load it if not present).
        >>> rjl['ec2']
        {
            # ...EC2's ResourceJSON as a dict...
        }

    """
    default_data_dirs = [
        DEFAULT_RESOURCE_JSON_DIR,
    ]

    def __init__(self, data_dirs=None):
        """
        Creates a new ``ResourceJSONLoader`` instance.

        :param data_dirs: (Optional) A list of absolute paths to check for the
            ResourceJSON. By default, this is just
            ``boto3.core.constants.DEFAULT_RESOURCE_JSON_DIR`` as the single
            item in the list.
        :type data_dirs: list
        """
        self.data_dirs = data_dirs
        self._loaded_data = {}

        if self.data_dirs is None:
            self.data_dirs = self.default_data_dirs

    def construct_filepath(self, path, service_name):
        """
        Constructs the expected path to load the JSON from.

        :param path: The absolute path to a data directory.
        :type path: string

        :param service_name: The name of the desired service
        :type service_name: string

        :returns: The full path to a (potential) JSON file
        """
        return os.path.join(path, "{0}.json".format(service_name))

    def load(self, service_name):
        """
        Loads the desired JSON for a service. (uncached)

        This will fall back through all the ``data_dirs`` provided to the
        constructor, returning the **first** one it finds.

        :param service_name: The name of the desired service
        :type service_name: string

        :returns: The loaded JSON as a dict
        """
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
        """
        Loads the desired JSON for a service. (cached)

        Identical to ``.load(...)``, this simply checks the cache first. If the
        data is found, no I/O is performed. If not, a ``.load(...)`` is
        performed, the result is cached & the data is then passed through.

        :param service_name: The name of the desired service
        :type service_name: string

        :returns: The loaded JSON as a dict
        """
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
