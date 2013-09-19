#!/bin/sh
export PYTHONPATH=`pwd`/..:`pwd`
nosetests -s -v --with-coverage --cover-package=boto3 --cover-html unit
