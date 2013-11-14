.. _sessions:

========
Sessions
========


Overview
========

``Session`` objects form the center of usage within ``boto``. It is a
lightweight store of all the configuration being used to talk to AWS. It stores
things like:

* region name
* access key
* secret key
* etc.

In addition, it also maintains a cache of the dynamic classes constructed to
talk to the AWS services.

You can have as many ``Session`` objects as needed. By default, ``boto``
includes a preconfigured instance as ``boto3.session`` as a useful shortcut,
though you can construct your own instances in needed/desired.

Common Usage
============

Common usage of the ``Session`` typically involves getting other,
service-related objects for usage. Things like ``Connection`` objects,
``Resource`` objects & ``Collection`` objects can all be fetched from a
configured ``Session``.

For example::

    >>> from boto3.session import Session
    >>> sess = Session()
    >>> s3_conn = sess.connect_to('s3', region_name='us-west-2')
    >>> BucketCollection = sess.get_collection('s3', 'BucketCollection')
    >>> BucketCollection(connection=s3_conn).all()
    {
        'buckets': [
            # ...Buckets here.
        ]
    }

The commonly used methods in ``Session`` are:

* ``.get_connection(...)``
* ``.connect_to(...)``
* ``.get_resource(...)``
* ``.get_collection(...)``


Common API
==========

For a complete list of API calls, please see :ref:`ref_core_session`.


``Session.get_connection(service_name)``
----------------------------------------

.. method:: Session.get_connection(self, service_name)

Retrieves a ``Connection`` **class**, which was either previously built or
will be constructed on demand. This class will feature methods for all the API
calls available for a given service.

Requires a ``service_name`` parameter, which should be a string of the service
to load. For example: ``sqs``, ``sns``, ``dynamodb``, etc.

Returns an **uninstantiated** class for that given service.


``Session.connect_to(service_name)``
------------------------------------

.. method:: Session.connect_to(self, service_name)

Nearly identical to ``Session.get_connection(...)``, except that it instead
returns an **instance** rather than the class itself.

This ``Connection`` instance is ready for immediate use.


``Session.get_resource(service_name, resource_name)``
-----------------------------------------------------

.. method:: Session.get_resource(self, service_name, resource_name)

Retrieves a ``Resource`` **class**, which was either previously built or
will be constructed on demand. This class will have methods on it for
communicating with a portion of a given service to which it is conceptually
mapped.

Requires a ``service_name`` parameter, which should be a string of the service
to load. For example: ``sqs``, ``sns``, ``dynamodb``, etc.

Requires a ``resource_name`` parameter, which should be a string of the resource
to load. For example: ``Queue``, ``Notification``, ``Table``, etc.

Returns an **uninstantiated** class for that given resource.


``Session.get_collection(service_name, collection_name)``
---------------------------------------------------------

.. method:: Session.get_collection(self, service_name, collection_name)

Retrieves a ``Collection`` **class**, which was either previously built or
will be constructed on demand. This class will have methods on it for
communicating with a portion of a given service to which it is conceptually
mapped.

Requires a ``service_name`` parameter, which should be a string of the service
to load. For example: ``sqs``, ``sns``, ``dynamodb``, etc.

Requires a ``collection_name`` parameter, which should be a string of the
collection to load. For example: ``QueueCollection``,
``NotificationCollection``, ``TableCollection``, etc.

Returns an **uninstantiated** class for that given collection.


Customizing
===========

.. warning::

    TBD
