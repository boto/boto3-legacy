class BotoException(Exception):
    """
    A base exception class for all Boto-related exceptions.
    """
    pass


class ServiceNotFound(BotoException):
    """
    Raised when the JSON mapping file for a service can not be found.

    Typically a file path issue.
    """
    pass


class NoSuchObject(BotoException):
    """
    Raised if a given object can't be found within a JSON service mapping.
    """
    pass
