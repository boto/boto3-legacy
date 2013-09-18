import logging


__author__ = 'Amazon Web Services'
__version__ = (0, 0, 1, 'alpha')


def get_version(full=False):
    """
    Returns a string-ified version number.

    Optionally accepts a ``full`` parameter, which if ``True``, will include
    any pre-release information. (Default: ``False``)
    """
    version = '.'.join([str(bit) for bit in __version__[:3]])

    if full:
        version = '-'.join([version] + list(__version__[3:]))

    return version


# Set up logging to ``/dev/null`` like a library is supposed to.
# http://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library
class NullHandler(logging.Handler):
    def emit(self, record):
        pass


log = logging.getLogger('boto3')
log.addHandler(NullHandler())
# End logging setup.


# A plain default ``Session`` (for convenience).
from boto3.core.session import Session
session = Session()
