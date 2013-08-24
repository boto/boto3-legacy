import os
import sys

from boto3 import get_version


# TODO: Assert if this is egg-safe (or if that matters to us)?
BOTO3_ROOT = os.path.dirname(__file__)

USER_AGENT = 'Boto3/{0} ({1})'.format(get_version(full=True), sys.platform)

DEFAULT_REGION = 'us-east-1'

DEFAULT_DOCSTRING = """
Please make an instance of this class to inspect the docstring.

No underlying connection is yet available.
"""


class NOTHING_PROVIDED(object):
    """
    An identifier for no data provided.

    Never meant to be instantiated.
    """
    pass


class NO_NAME(object):
    """
    An identifier to indicate a method instance hasn't been given a name.

    Never meant to be instantiated.
    """
    pass


class NO_RESOURCE(object):
    """
    An identifier to indicate a method instance hasn't been attached to a
    resource.

    Never meant to be instantiated.
    """
    pass
