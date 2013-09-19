"""
Some commonly used things that aren't bundled with (all versions of) Python.

We'll lean on botocore for them, to limit the amount of duplication.
"""
from botocore.compat import json
from botocore.compat import OrderedDict
from botocore.compat import six
