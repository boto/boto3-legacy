class BotoException(Exception):
    """
    A base exception class for all Boto-related exceptions.
    """
    pass


class NoSuchMethod(BotoException):
    pass
