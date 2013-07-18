import botocore.session


class Session(object):
    """
    FIXME: Potentially wrap the ``botocore`` session.

    """
    def __init__(self, session=None):
        self.core_session = session

        if not self.core_session:
            self.core_session = botocore.session.get_session()

    def get_service(self, service_name):
        return self.core_session.get_service(service_name)


# For the lazy.
# TODO: We may not want to support this. OTOH, it'd be super-convenient &
#       optional.
default_session = Session()
