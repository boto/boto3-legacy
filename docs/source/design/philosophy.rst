.. ref: design_philosophy

==========
Philosophy
==========

In a nutshell, the goals of ``boto`` are:

* provide a convenient/friendly interface to `AWS`_
* support both Python 2 & Python 3 in the same codebase
* supply an interface that is:

    * Pythonic
    * consistent
    * easy to use

* excellent test coverage
* solid documentation

.. _`AWS`: http://aws.amazon.com/


Convenient/Friendly Interface To AWS
====================================

Using ``boto`` should **always** be easier that having to write the equivalent
code to make a request yourself. We do this by providing:

* All the necessary request signing components
* Automatic retry support
* Connection pooling
* Handling most aspects of the serialization/deserialization for you


Support Python 2 & 3
====================

We support a wide range of Python installations, from the older Python 2.6/2.7
series to the most recent releases of Python 3.3 & beyond. This is doable
within a single codebase (see examples like ``aws-cli``, ``botocore`` & many
popular community projects such as ``requests``, ``SQLAlchemy`` & ``Django``)
without requiring tools lik ``2to3``.

We will use things like ``six`` & our own wrappers to ensure that we write the
code once & it works on all Python versions we support.


Pythonic, Consistent, Easy-To-Use Interface
===========================================

This comes from history/experience. ``boto`` (up until v3) had different,
hand-written implementations for each service. Each could vary (sometimes quite
widely) from one another. While this was simply a product of history, this made
it more difficult to maintain & required the user to reference documentation
(or the source) often.

We'll be making an attempt to standardize the interfaces as much as makes sense
to do, while recognizing this is a balancing act & that some differences can be
justified. So common interactions between services should look similar when
used from ``boto`` (a ``create`` in one service should look like a ``create``
in another).

We'll also be taking this opportunity to reuse code (as well as a
data-driven service/object layer) to make ``boto`` easier to maintain & keep
up-to-date.

Finally, use of ``boto`` should feel comfortable/familiar to programmers used
to the way Python (as well as other libraries) makes APIs available. The
"Zen of Python" will be clutched firmly in our grasp.


Excellent Test Coverage
=======================

Another lesson of history, when approaching something this complex, good test
coverage can make all the difference in preventing regressions & ensuring
quality. We'll be striving for >90% test coverage on all core functionality.

For integration, we'll be making a best effort & striving to find better ways
to cover more of the services' APIs.


Solid Documentation
===================

Finally, software provided without documentation does neither the end user nor
the developer of the software any benefit. It is infuriating to have to
endlessly source-dive to figure out how to use something as well as being
unmaintainable to handle all support requests/questions surrounding usage of
undocumented code.

We will do our best to ensure all public APIs have docstrings, that we include
reference docs for all of the API, that many services will have their own
tutorials & that we provide guidance on configuring & extending the software
we're providing.
