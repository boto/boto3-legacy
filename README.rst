=====
boto3
=====

An evolution of boto, supporting both Python 2 & 3.

**WARNING**: This repo is very unstable & the API **WILL** shift as time goes
on. This code is **NOT** yet production-ready.


Requirements
============

* Python 2.6+ or Python 3.3+
* botocore==0.12.0
* six>=1.1.0
* jmespath==0.0.2
* python-dateutil>=2.1


Running Tests
=============

Setup looks like:

    $ virtualenv -p python3 env3
    $ . env3/bin/activate
    $ pip install -r requirements.txt
    $ pip install nose

Running tests looks like:

    $ nosetests -s -v unit

**WARNING:** Running integration tests requires a valid AWS account & **WILL**
result in charges to that account based on usage.
