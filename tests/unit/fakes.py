import glob
import os

import botocore.session

from boto3.constants import AWS_JSON_PATHS
from boto3.session import Session
from boto3.utils import json


FAKE_JSON = {
    "TestObject": {
        "mappings": {
            "create": {
                "client_method": "CreateTestObject",
                "client_parameters": {
                    "Stuff": {
                        "required": False,
                        "source_from": "parameter",
                        "variable": "stuff"
                    },
                    "Name": {
                        "required": True,
                        "source_from": "instance",
                        "variable": "name"
                    }
                },
                "parameters": {
                    "stuff": {
                        "required": False,
                        "type": "map"
                    }
                },
                "result": {
                    "Whatever": {
                        "behavior": "store_instance",
                        "store_as": "whatever"
                    },
                    "Something.Else": {
                        "behavior": "store_instance",
                        "store_as": "something_else"
                    }
                }
            },
            # FIXME: Add another method here?
        }
    }
}


class Trackable(object):
    def __init__(self, *args, **kwargs):
        self._calls = []
        self._parent = None

    def __getattr__(self, name):
        self._calls.append({
            'method': '__getattribute__',
            'args': [name],
            'kwargs': {},
        })
        return self

    def __call__(self, *args, **kwargs):
        self._calls.append({
            'method': self.__dict__.get('__new_name__', 'Unnamed'),
            'args': args,
            'kwargs': kwargs,
        })


class FakeClient(Trackable):
    def __getattribute__(self, name):
        trackable = Trackable()
        trackable.parent = self
        trackable.__new_name__ = name
        return trackable


class FakeSession(Session):
    _json_cache = {}
    _session = botocore.session.get_session()

    def __init__(self, *args, **kwargs):
        kwargs['core_session'] = FakeSession._session
        super(FakeSession, self).__init__(*args, **kwargs)

        # For performance, only load the JSON files once.
        if not FakeSession._json_cache:
            FakeSession._populate_json_cache()

    def load_json_for(self, service):
        return FakeSession._json_cache.get(service, {})

    @classmethod
    def _populate_json_cache(cls):
        paths = os.path.join(AWS_JSON_PATHS[-1], "*.json")

        for path in glob.glob(paths):
            service, _dot_json = os.path.splitext(os.path.basename(path))

            with open(path, 'r') as json_file:
                FakeSession._json_cache[service] = json.load(json_file)

        # Lastly, shove it a purely testing example.
        cls._json_cache['testing'] = FAKE_JSON
