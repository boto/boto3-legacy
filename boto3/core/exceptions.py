class BotoException(Exception):
    """
    A base exception class for all Boto-related exceptions.
    """
    pass


class ServerError(BotoException):
    """
    Thrown when an error is received within a response.
    """
    fmt = "[{0}]: {1}"

    def __init__(self, code='GeneralError', message='No message',
                 full_response=None, **kwargs):
        self.code = code
        self.message = message
        self.full_response = full_response

        if self.full_response is None:
            self.full_response = {}

        msg = self.fmt.format(
            self.code,
            self.message
        )
        super(ServerError, self).__init__(msg)


class IncorrectImportPath(BotoException):
    pass


class NoSuchMethod(BotoException):
    pass


class NotCached(BotoException):
    pass


class ResourceError(BotoException):
    pass


class NoResourceJSONFound(ResourceError):
    pass


class APIVersionMismatchError(BotoException):
    pass


class NoRelation(ResourceError):
    pass


class ValidationError(BotoException):
    pass


class MD5ValidationError(ValidationError):
    pass
