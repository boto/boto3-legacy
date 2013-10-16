from boto3.core.exceptions import APIVersionMismatchError


class ResourceBase(object):
    """
    Abstracts some of the common logic between ``ResourceCollection`` &
    ``Resource``.

    Specifically, this handles dynamically updating the docstrings & doing
    the API version checking.
    """
    # Subclasses should always specify this & list out the API versions
    # it supports.
    valid_api_versions = []

    def _update_docstrings(self):
        # Because this is going to get old typing & re-typing.
        cls = self.__class__

        for attr_name, method in cls._methods.items():
            method.update_docstring(self)

    def _check_api_version(self):
        # ALL THE UNDERS!!!
        conn_version = self._connection._details.api_version

        if not conn_version in self.valid_api_versions:
            msg = "The '{0}' resource supports these API versions ({1}) " + \
                  "but the provided connection has an incompatible API " + \
                  "version '{2}'."
            raise APIVersionMismatchError(
                msg.format(
                    self.__class__.__name__,
                    ', '.join(self.valid_api_versions),
                    conn_version
                )
            )