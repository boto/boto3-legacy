try:
    # Attempt to use ``simplejson`` where available, for speed.
    import simplejson as json
except ImportError:
    # Fall back to the built-in ``json`` module.
    import json

from botocore.compat import OrderedDict
