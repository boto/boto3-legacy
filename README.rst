=====
boto3
=====

An evolution of boto, supporting both Python 2 & 3.

This is not a port of boto_, but a ground-up rewrite. We hope to improve on boto
in both consistency & maintainability.

**WARNING**: This repo is very unstable & the API **WILL** shift as time goes
on. This code is **NOT** yet production-ready. When the code is closer to ready
for public consumption, we'll enable the GitHub issues on the repo.

.. _boto: https://docs.pythonboto.org/


Requirements
============

* Python 3.3+ first, but also works on Python 2.6+
* botocore==0.16.0
* six>=1.4.0
* jmespath>=0.0.2
* python-dateutil>=2.1


Current Status
==============

Complete
--------

* Low-level ``Connection`` objects are relatively complete (need docstring work
  and better argument handling if we can), but are usable *now*.

    * These are equivalent to the low-level ``*Connection`` objects in boto.
    * Relatively finalized, though they may eventually move down to botocore_
      (still importable & usable in ``boto3`` though).

.. _botocore: https://github.com/boto/botocore

In-progress
-----------

* ``Resource`` objects

    * A more Pythonic/object-y layer on top of the ``Connection`` objects
    * Easier/more natural to work with
    * Basic calls function, but you need to supply all parameters the right way
      (leaning on the API docs a lot) & the responses are pretty raw
    * Needs more response parsing work

* ``ResourceCollection`` objects

    * Abstracts working with collections of ``Resource`` objects
    * Basic functionality kinda works (creates/gets data) but not very useful
      yet


Running Tests
=============

Setup looks like::

    $ virtualenv -p python3 env3
    $ . env3/bin/activate
    $ pip install -r requirements.txt
    $ pip install nose

Running tests looks like::

    $ nosetests -s -v unit

**WARNING:** Running integration tests (``nosetests -s -v integration``)
requires a valid AWS account & **WILL** result in charges to that account
based on usage.
