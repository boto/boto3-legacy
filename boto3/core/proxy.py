class Proxy(object):
    """
    A proxy object to wrap/delay calls.

    Usage::

        >>> from boto3.s3.resources import S3ObjectCollection
        >>> s3_col = S3ObjectCollection()

        # First, specify a target to operate on & pass in any parameters you'd
        # like bound to the final invocation.
        >>> proxy_s3_col = Proxy(target=s3_col, kwargs={'bucket': 'hello'})

        # You can update it as time goes on.
        >>> proxy_s3_col.kwargs['max-keys'] = 10

        # Finally, finish the call just like you're working with the original
        # object.
        # The parameters you've already set up will be applied.
        >>> proxy_s3_col.all()
        [
            # ...
        ]

    """
    def __init__(self, target, args=None, kwargs=None):
        """
        Creates a Proxy instance.

        :param target: The initial object to start with.
        :type target: object

        :param args: (Optional) The positional arguments to apply to the final
            call. Default is ``None``.
        :type args: list

        :param kwargs: (Optional) The keyword arguments to apply to the final
            call. Default is ``None``.
        :type kwargs: dict
        """
        self.target = target
        self.args = []
        self.kwargs = {}

        if args:
            self.args = list(args)

        if kwargs:
            self.kwargs = kwargs

    def __getattr__(self, name):
        attr = getattr(self.target, name)

        if callable(attr):
            self.target = getattr(self.target, name)
            return self
        else:
            return attr

    def __call__(self, *args, **kwargs):
        self.args.extend(args)
        self.kwargs.update(kwargs)
        return self.target(*self.args, **self.kwargs)
