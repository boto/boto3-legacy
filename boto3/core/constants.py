import os
import sys

from boto3 import get_version


# TODO: Assert if this is egg-safe (or if that matters to us)?
BOTO3_ROOT = os.path.dirname(__file__)

USER_AGENT = 'Boto3/{0} ({1})'.format(get_version(full=True), sys.platform)

DEFAULT_REGION = 'us-east-1'


class NOTHING_PROVIDED(object):
    """
    A identifier for no data provided.

    Never meant to be instantiated.
    """
    pass


class NOTHING_RECEIVED(object):
    """
    A identifier for no data received.

    Never meant to be instantiated.
    """
    pass
