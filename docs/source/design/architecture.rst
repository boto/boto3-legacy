.. _design_architecture:

============
Architecture
============

The design of ``boto`` uses a very layered approach. These layers can be
broadly categorized as follows (from lowest level to highest level):

* Underlying (``botocore``)
* ``Connections``
* ``Resources`` & ``Collections``
* ``Convenience``

Each layer (with the exception of the ``Convenience`` layer) has been designed
to both provide maximum API coverage for a given service, as well as providing
the user the opportunity to drop down to a lower-level should they need it.

Additionally, ``boto`` makes use of several other pieces of infrastructure
(which tend to be more broadly applied) to help make a cohesive whole:

* ``Session`` objects
* ``Introspection``
* ``Waiter`` objects

A more complete description of each layer/component can be found below.


Broad Ideas
===========

* The ``Connections`` & ``Resource/Collections`` layers are highly-dynamic,
  being built from either introspection (``Connections``) or data
  (``Resources/Collections``, in the form of JSON).
* We use `factories`_ to generate much of the ``Connection`` & ``Resource``
  (as opposed to metaclassing or code generation), because they have proven to
  be:

    * Easier to read & maintain (over metaclasses)
    * Do not change at import time (over metaclasses)
    * Are most flexible in the face of end-user alterations (over code
      generation)

* We will provide hooks for extending/overriding behavior in every area that
  makes sense.
* We will make it as easy as is reasonable for the user to drop down to a lower
  layer should it be necessary (for instance, any given ``Resource`` ought to
  have a pre-configured ``Connection`` as an instance variable the end-user
  can use).

.. _`factories`: http://en.wikipedia.org/wiki/Factory_method_pattern


Layers
======

Underlying (``botocore``)
-------------------------

``botocore`` provides much of the actual over-the-wire functionality. It
handles:

* the signing of requests,
* the serialization/deserialization of responses,
* validation of parameters,
* error-handling,
* retry support
* as well as many other things.

All interactions with AWS can be done through ``botocore``. However, doing
so is relatively tedious, repetitive & requires intimate knowledge of the given
service. Each call requires instantiating  an ``Operation`` instance (as well as
other objects) & constructing a proper body, then parsing through a
dictionary of returned data.

The "raison d'etre" of ``boto`` is to add API on top of this, making it easier
to perform requests & handle the returning data.

For more information, please consult the `botocore`_ documentation.

.. _`botocore`: http://botocore.readthedocs.org/en/latest/


``Connection`` Layer
--------------------

The ``Connection`` layer is a step above the "Underlying" layer. Each
``Connection`` object covers the entire API of a given service (for instance,
``Ec2Connection`` covers all of the Amazon Elastic Compute Cloud service's API
calls).

A ``Connection`` object is typically built via a ``ConnectionFactory`` instance.
The only things that are required are a configured ``Session`` & a service
name (i.e. ``dynamodb``).

The ``Connection`` layer will get the ``Service`` from ``botocore`` &
introspect all of the operations/API calls that can be performed for that
service. It then has nice wrappers applied around all of the methods, making
it convenient to make a variety of API calls.

For convenience, a ``Session`` object has a convenience method for constructing
a connection called ``.connect_to(...)``.

Example usage of getting & using a ``Connection`` looks like::

    >>> import boto3
    # Using the default ``session``. See the ``Session`` documentation for more
    # information on if you should use this.
    >>> s3_conn = boto3.session.connect_to('s3')
    # Now that we have a ``Connection``, call operations.
    >>> s3_conn.create_bucket(name='my_unique_bucket_name')
    { ... Response data ... }
    >>> s3_conn.create_object(
    ...     bucket_name='my_unique_bucket_name',
    ...     key='hello_world.txt',
    ...     content="Hello, world!"
    ... )
    { ... Response data ... }

However, the data you pass is still relatively low-level, all parameters for a
given call must be passed (no use of instance data) & all responses are very
"raw" (little to no post-processing done beyond deserialization).

See the :ref:`connections` documentation for more information on how to
extend/override behavior, or the service tutorials for examples on usage of
a given ``Connection``.


``Resources`` & ``Collections`` Layer
-------------------------------------

The next layer up from ``Connections`` is the ``Resources/Collections`` layer.
This layer utilizes the ``Connections`` for all the API calls.

However, in contrast to the ``Connection`` layer, the ``Resource`` layer looks
much more like traditional Python objects, where a given ``Resource`` covers
a conceptual area rather than every API call available. For example, an EC2
``Instance`` covers all API calls that relate to the manipulation of a
single EC2 instance, but does not handle things like creating an ELB instance.

A ``Collection`` is a list/grouping, typically paired with a ``Resource``. It
handles things like returning all individual instances, creating a new instance
or getting a specific one by identifier.

A ``Resource``, on the other hand, is a single instance within a service. Things
like updating information or deleting a resource are typically done on these
instances.

Both ``Collections`` & ``Resources`` are also built with factories
(``CollectionFactory`` & ``ResourceFactory``), but they do **NOT** introspect
the lower-level objects. They are instead built off of a JSON-powered data
format (called ``ResourceJSON``), which describes what methods/data make up a
given object.

Again, a given ``Session`` object has convenience methods for constructing
a collection (``.get_collection(...)``) or resource (``.get_resource(...)``).

Example usage of getting & using a ``Collection/Resource`` looks like::

    >>> import boto3
    # Using the default ``session``. See the ``Session`` documentation for more
    # information on if you should use this.
    >>> BucketCollection = boto3.session.get_collection('s3', 'BucketCollection')
    # Now we'll create a bucket.
    >>> bucket = BucketCollection().create(
    ...     name='my_unique_bucket_name'
    ... )
    # We get back a ``Bucket`` *resource* for use.
    >>> type(bucket)
    <class Bucket>
    # They also know about related classes they can create.
    # For example, we can create an ``S3Object`` from here.
    >>> key = bucket.objects.create(
    ...     key='hello_world.txt',
    ...     content="Hello, world!"
    ... )
    # These feature instance data, rather than raw returned data.
    >>> key.name
    'hello_world.txt'

This improves on the ``Connection`` layer by using instance data where
available, populating new ``Resource`` objects as needed, having relations with
other ``Resources`` or ``Collections`` for easy access & looks more like
traditional objects.

See the :ref:`resources_collections` documentation for more information
on how to extend/override behavior, or the service tutorials for examples on
usage of a given ``Resource/Collection``.


``Convenience`` Layer
---------------------

.. warning::

    TBD.


General Infrastructure
======================

``Session`` Objects
-------------------

The ``Session`` encapsulates the configuration information for a given set of
API calls. It contains information like what `region`_ you're connecting to,
what API keys you're using, etc.

.. warning::

    We may need to revise the above, since we don't actually store that for the
    moment, though the session makes it easier to handle & pass on those
    things.

It also keeps a cache of all the ``Connection/Resource/Collection`` classes it
creates, to reduce time spent rebuilding previously seen classes & to make
relations between high-level objects work (without requiring a global store
of the data).

``Session`` classes are relatively lightweight (most of the bulk is their
object caches) & you're free to have as many of them as you'd like/need.

Example usage::

    >>> from boto3.session import Session
    >>> my_session = Session()

``boto`` ships with a default ``Session``, instantiated as ``boto3.session``.
See :ref:`sessions` documentation for more information
on how to extend/override behavior.

.. _`region`: http://docs.aws.amazon.com/general/latest/gr/rande.html

``Introspection``
=================

This set of objects allows the ``Connection`` layer to introspect the
``botocore`` service data. While not generally used by the end-user, it may
be useful if you require more information about a given service or wish to make
using ``botocore`` directly easier.

Please refer to the reference documentation for more information.


``Waiter`` Objects
==================

The ``Waiter`` objects (sometimes called the `Polling Consumer`_ pattern)
provide a way to handle the frequently eventually-consistent nature of many
AWS services. Because a given API call may take time (for instance, spinning
up an EC2 instance), any further client calls may fail until a given resource
is ready.

To combat this (& the need for the end user to manage either sleeping or
polling themselves), we incorporated ``Waiter`` objects at the
``Resource/Collection`` level. This provides a familiar blocking-style
interface, ensuring that subsequent calls have a valid resource to be talking
to.

Under the hood, this simply does a busy-loop, sleeping & polling until the
given resource is either ready or has errored.

Example::

    >>> from boto3.core.waiters import Waiter

.. warning::

    TBD.

.. _`Polling Consumer`: http://www.eaipatterns.com/PollingConsumer.html
