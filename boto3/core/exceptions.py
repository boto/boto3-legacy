class BotoException(Exception):
    """
    A base exception class for all Boto-related exceptions.
    """
    pass


class NoSuchMethod(BotoException):
    pass


class ResourceError(BotoException):
    pass


class NoNameProvidedError(BotoException):
    pass


class NoResourceAttachedError(BotoException):
    pass


class ValidationError(BotoException):
    pass


class MD5ValidationError(ValidationError):
    pass
