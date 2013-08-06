# -*- coding: utf-8 -*-
import time


class WaiterException(Exception):
    pass


class RetriesExceededError(WaiterException):
    pass


class TimeoutExceededError(WaiterException):
    pass


class Waiter(object):
    """
    An object that blocks until a condition is met or an error occurs.

    It immitates a subset of the ``Thread`` API.

    Example::

        # The simple case.
        # What would have been ``client.create_cluster('my_cluster_id')``...
        >>> waiter = Waiter(
        ...     target=client.create_cluster,
        ...     args=['my_cluster_id']
        ... )
        # Enter the busy loop.
        >>> waiter.join()

        # A complex example.
        >>> def before_running(waiter_obj):
        ...     print "About to attempt %s..." % waiter_obj.target

        >>> def before_sleeping(waiter_obj):
        ...     print "Whelp, that didn't work. Sleeping for %s..." % waiter.interval

        >>> waiter = Waiter(
        ...     target=client.create_cluster,
        ...     args=[
        ...         'my_cluster_id',
        ...         'dw.hs1.xlarge',
        ...     ],
        ...     kwargs={
        ...         'number_of_nodes': 4,
        ...         'master_username': 'whatever',
        ...     },
        ...     retries=1,
        ...     interval=0.5
        ... )
        >>> waiter.join(
        ...     before_attempt=before_running,
        ...     before_wait=before_sleeping
        ... )

    """
    retries = 3
    interval = 60

    def __init__(self, target, args=None, kwargs=None, retries=None,
                 interval=None):
        """
        Sets up the ``Waiter`` instance.

        Requires a ``target`` argument, which should be the callable to execute.

        Accepts an optional ``args`` argument, which should be a list of
        arguments to pass to the callable. Default is ``None`` (nothing passed).

        Accepts an optional ``kwargs`` argument, which should be a dictionary
        of keyword arguments to pass to the callable. Default is ``None``
        (nothing passed).

        Accepts an optional ``retries`` argument, which is the number of times
        to retry the call. It should be an integer greater than or equal to 0.
        Default is ``3``.

        Accepts an optional ``interval`` argument, which is the number of
        seconds to sleep in-between calls. It should be a float greater than
        or equal to 0. Default is ``60``
        """
        super(Waiter, self).__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

        if self.args is None:
            self.args = []

        if self.kwargs is None:
            self.kwargs = {}

        # Check against ``None``, because 0 is a valid number of retries.
        if retries is not None:
            retries = int(retries)

            if retries < 0:
                raise ValueError(
                    "Retries must be greater than 0. Got %s." % retries
                )

            self.retries = retries

        # Check against ``None``, because 0 is a valid (though ill-advised)
        # interval number.
        if interval is not None:
            interval = float(interval)

            if interval < 0:
                raise ValueError(
                    "Interval must be greater than 0. Got %s." % interval
                )

            self.interval = interval

    def join(self, before_attempt=None, before_wait=None, timeout=None):
        """
        Attempts to run the callable until either it succeeds or the number
        of retries is exceeded.

        Optionally accepts a ``before_attempt`` argument, which should be a
        callable object/function. It is provided as a hook, which is called
        right before the configured callable is run. It will receive one
        parameter, the ``waiter`` instance that's calling it. Default is
        ``None``.

        Optionally accepts a ``before_wait`` argument, which should be a
        callable object/function. It is provided as a hook, which is called
        right before the ``Waiter`` instance will sleep. It will receive one
        parameter, the ``waiter`` instance that's calling it. Default is
        ``None``.
        """
        # Increment by one, so that we make it through the loop at least once.
        times_to_retry = self.retries + 1
        start_time = time.time()

        for retry_count in range(times_to_retry):
            if timeout is not None:
                elapsed = time.time() - start_time

                if elasped >= timeout:
                    raise TimeoutExceededError(
                        "%r exceeded the timeout of %s." % (
                            self.target,
                            timeout
                        )
                    )

            if before_attempt:
                # TODO: Do we need error/success handling, or should this just
                #       be a hook?
                before_attempt(self)

            success = self.target(*self.args, **self.kwargs)

            if success:
                # The condition has been met & we're done here. Bail out.
                return success

            if before_wait:
                # TODO: Do we need error/success handling, or should this just
                #       be a hook?
                before_wait(self)

            # Take a dirt nap.
            time.sleep(self.interval)

        # If we make it here, we've exceeded the number of retries we're
        # supposed to exeucte. Raise an exception & bomb out!
        raise RetriesExceededError(
            "%r exceeded the number of retries (%s) allowed." % (
                self.target,
                self.retries
            )
        )
