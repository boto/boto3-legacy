import os

import botocore.session

from boto3.constants import AWS_JSON_PATHS
from boto3.exceptions import ServiceNotFound
from boto3.utils import json


class Session(object):
    """
    The object that ties together a boto3 session.

    All high-level objects come from this object.

    Usage::

        from boto3.session import Session

        session = Session()
        sqs_json = session.load_json_for('sqs')

    """
    def __init__(self, json_paths=None, core_session=None):
        self._object_cache = {}
        self.json_paths = json_paths
        self.core_session = core_session

        if not self.json_paths:
            self.json_paths = AWS_JSON_PATHS

        if not self.core_session:
            self.core_session = botocore.session.get_session()

    def load_json_for(self, service):
        filename = '{0}.json'.format(service)

        # Traverse the possible paths the JSON could be on, falling back on
        # increasingly more generic paths.
        for path in self.json_paths:
            file_path = os.path.join(path, filename)

            if os.path.exists(file_path):
                with open(file_path, 'r') as json_file:
                    return json.load(json_file)

        raise ServiceNotFound(
            "A service mapping file for '{0}'".format(service) +
            " could not be found on any of the JSON paths."
        )

    def get_client(self, service):
        return self.core_session.get_service(service)


# For the lazy.
# TODO: We may not want to support this. OTOH, it'd be super-convenient &
#       optional.
default_session = Session()
