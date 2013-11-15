.. _connections:

===========
Connections
===========


Overview
========

``Connection`` objects form the basis of most API calls to AWS. They are
utilized & built upon by every other layer within ``boto``.

In turn, they're actually simply a light wrapper over the top of underlying
``botocore`` `Operation`_ objects. The benefit they provide over just utilizing
those objects is that a single ``Connection`` object has all the methods a
given AWS service responds to present on a single, easy-to-use object.

.. _`Operation`: http://botocore.readthedocs.org/en/latest/tutorial/ec2_examples.html#a-simple-ec2-example


Where Are The Connections?
==========================

Unlike ``Connection`` objects in ``boto`` prior to the release of
version 3.0.0, there aren't any concrete ``Connection`` subclasses defined
within ``boto`` source. You won't find the following anywhere within ``boto``::

    class S3Connection(Connection):
        # ...

This is because all ``Connection`` objects are **generated** at **run-time**.
They are constructed on-the-fly when you request them.

This is done because the underlying ``botocore`` objects are based on a
(user-customizable) JSON data format that describes the services. By editing
or overriding the JSON, you can modify how ``botocore`` & ``boto`` behave.

However, as a result, this means that the only way to ensure correct behavior
is to also have the higher-level interfaces built off those objects. If we
defined concrete classes, we'd risk drift between what the JSON format provides
& how our classes behave.

To avoid that drift, we generate the classes on request. See the
:ref:`Construction <connection_construction>` section for more information.


Usage
=====

Using a connection is relatively straightforward once you have a class
constructed. It also varies widely between services, as the services rarely
expose common calls between them.

.. warning::

    TBD


.. _connection_construction:

Construction
============

Construction of ``Connection`` objects takes place within a
``boto3.core.connection.ConnectionFactory`` instance. Any instance (whether
built into ``boto`` or instantiated by a user) can successfully create
``Connection`` subclasses.

Usage is trivial::

    >>> import boto3
    >>> from boto3.core.connection import ConnectionFactory
    # We'll use the default session, though you can just as easily provide
    # your own custom ``Session`` instance.
    >>> cf = ConnectionFactory(session=boto3.session)
    # Now build the connection.
    >>> S3Connection = cf.construct_for('s3')

However, to make things even easier, this functionality is also exposed through
the :ref:`Session <sessions>` object itself. The ``Session`` has it's
own ``ConnectionFactory`` instance(s) & can handle the details for you.

So typically, you'll actually do::

    >>> import boto3
    # Again, we're just using the default session, but you should feel free
    # to use your own ``Session`` instances.
    >>> S3Connection = boto3.session.get_connection('s3')

Now ``S3Connection`` is ready to be instantiated & you'll be able to talk to
`S3`_!

.. _`S3`: http://aws.amazon.com/s3/


Under The Hood
--------------

So how does the ``ConnectionFactory`` actually *build* these classes? It's a
combination of several objects: the ``ConnectionFactory`` itself, the
``Connection`` base class & the ``ConnectionDetails`` class.

The ``ConnectionFactory`` handles the overall construction. It first builds
a ``ConnectionDetails`` instance. This instance is given the ``service_name``,
which allows the class (via introspection) to discover what service data is
available from the underlying ``botocore`` objects.

The ``ConnectionFactory`` then builds a class name (such as ``S3Connection``,
``Ec2Connection`` or ``DynamodbConnection``, etc.).

Next, the ``ConnectionFactory`` builds up a dictionary of all the service
methods that will need to be added to the class. It does this by asking the
``ConnectionDetails`` class for all the service data, getting a dictionary of
of method names & operation information back. It iterates over this &
dynamically builds methods, which the ``ConnectionFactory`` hangs onto
temporarily.

Finally, the ``ConnectionFactory`` constructs a brand new class (using
``type(...)`` plus all the attributes/methods/``ConnectionDetails`` instance).
It then provides this class back to the user, a fully-built Python class with
all the service methods & docs available.


Overriding/Extending
====================

There are several hooks built into the ``ConnectionFactory`` to customize
how it builds classes.

First, you can specify your own base ``Connection`` class. This allows you to
alter the behavior of *every* connection that comes out of the factory. This
class should be passed as an initialization parameter to the
``ConnectionFactory``.

For example::

    import logging
    from boto3.core.connection import Connection, ConnectionFactory

    LOG = logging.getLogger(__file__)


    class LoggedConnection(Connection):
        def __init__(self, *args, **kwargs):
            LOG.debug("Instantiated a connection for {0}".format(
                self._details.service_name
            ))
            super(LoggedConnection, self).__init__(*args, **kwargs)


    cf = ConnectionFactory(base_connection_class=LoggedConnection)
    S3Connection = cf.construct_for('s3')
    assert issubclass(S3Connection, LoggedConnection)

You can do a similar thing for the ``ConnectionDetails`` class to be used. It
also is specified as part of the initialization of a ``ConnectionFactory``.

For example::

    from boto3.core.connection import ConnectionDetails, ConnectionFactory


    class UndeletableConnectionDetails(ConnectionDetails):
        @property
        def service_details(self):
            details = super(UndeletableConnectionDetails, self).service_details

            # Use ``list`` to make a copy under Py3, so that the dictionary
            # isn't what's being iterated over (since we're deleting data).
            for operation_name in list(details.keys()):
                if 'delete' in operation_name:
                    del details[operation_name]

            return details


    cf = ConnectionFactory(details_class=UndeletableConnectionDetails)
    S3Connection = cf.construct_for('s3')
    assert not hasattr(S3Connection, 'delete_bucket')

