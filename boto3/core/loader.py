import glob
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

    def get_available_options(self, service_name):
        """
        Fetches a collection of all JSON files for a given service.

        This checks user-created files (if present) as well as including the
        default service files.

        Example::

            >>> loader.get_available_options('s3')
            {
                '2013-11-27': [
                    '~/.boto-overrides/s3-2013-11-27.json',
                    '/path/to/boto3/data/aws/resources/s3-2013-11-27.json',
                ],
                '2010-10-06': [
                    '/path/to/boto3/data/aws/resources/s3-2010-10-06.json',
                ],
                '2007-09-15': [
                    '~/.boto-overrides/s3-2007-09-15.json',
                ],
            }

        :param service_name: The name of the desired service
        :type service_name: string

        :returns: A dictionary of api_version keys, with a list of filepaths
            for that version (in preferential order).
        :rtype: dict
        """
        options = {}

        for data_dir in self.data_dirs:
            # Traverse all the directories trying to find the best match.
            service_glob = "{0}-*.json".format(service_name)
            path = os.path.join(data_dir, service_glob)
            found = glob.glob(path)

            for match in found:
                # Rip apart the path to determine the API version.
                base = os.path.basename(match)
                bits = os.path.splitext(base)[0].split('-', 1)

                if len(bits) < 2:
                    continue

                api_version = bits[1]
                options.setdefault(api_version, [])
                options[api_version].append(match)

        return options

    def get_best_match(self, options, service_name, api_version=None):
        """
        Given a collection of possible service options, selects the best match.

        If no API version is provided, the path to the most recent API version
        will be returned. If an API version is provided & there is an exact
        match, the path to that version will be returned. If there is no exact
        match, an attempt will be made to find a compatible (earlier) version.

        In all cases, user-created files (if present) will be given preference
        over the default included versions.

        :param options: A dictionary of options. See
            ``.get_available_options(...)``.
        :type options: dict

        :param service_name: The name of the desired service
        :type service_name: string

        :param api_version: (Optional) The desired API version to load
        :type service_name: string

        :returns: The full path to the best matching JSON file
        """
        if not options:
            msg = "No JSON files provided. Please check your " + \
                  "configuration/install."
            raise NoResourceJSONFound(msg)

        if api_version is None:
            # Give them the very latest option.
            best_version = max(options.keys())
            return options[best_version][0], best_version

        # They've provided an api_version. Try to give them exactly what they
        # requested, falling back to the best compatible match if no exact
        # match can be found.
        if api_version in options:
            return options[api_version][0], api_version

        # Find the best compatible match. Run through in descending order.
        # When we find a version that's lexographically less than the provided
        # one, run with it.
        for key in sorted(options.keys(), reverse=True):
            if key <= api_version:
                return options[key][0], key

        raise NoResourceJSONFound(
            "No compatible JSON could be loaded for {0} ({1}).".format(
                service_name,
                api_version
            )
        )

    def load(self, service_name, api_version=None, cached=True):
        """
        Loads the desired JSON for a service. (uncached)

        This will fall back through all the ``data_dirs`` provided to the
        constructor, returning the **first** one it finds.

        :param service_name: The name of the desired service
        :type service_name: string

        :param api_version: (Optional) The desired API version to load
        :type service_name: string

        :param cached: (Optional) Whether or not the cache should be used
            when attempting to load the data. Default is ``True``.
        :type cached: boolean

        :returns: The loaded JSON as a dict
        """
        # Fetch from the cache first if it's there.
        if cached:
            if service_name in self._loaded_data:
                if api_version in self._loaded_data[service_name]:
                    return self._loaded_data[service_name][api_version]

        data = {}
        options = self.get_available_options(service_name)
        match, version = self.get_best_match(
            options,
            service_name,
            api_version=api_version
        )

        with open(match, 'r') as json_file:
            data = json.load(json_file)
            # Embed where we found it from for debugging purposes.
            data['__file__'] = match
            data['api_version'] = version

        if cached:
            self._loaded_data.setdefault(service_name, {})
            self._loaded_data[service_name][api_version] = data

        return data

    def __contains__(self, service_name):
        return service_name in self._loaded_data


# Default instance for convenience.
default_loader = ResourceJSONLoader()
