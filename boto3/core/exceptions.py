class BotoException(Exception):
    """
    A base exception class for all Boto-related exceptions.
    """
    pass


class IncorrectImportPath(BotoException):
    pass


class NoSuchMethod(BotoException):
    pass


class ResourceError(BotoException):
    pass


class APIVersionMismatchError(BotoException):
    pass


class NoNameProvidedError(BotoException):
    pass


class NoResourceAttachedError(BotoException):
    pass


class ValidationError(BotoException):
    pass


class MD5ValidationError(ValidationError):
    pass
