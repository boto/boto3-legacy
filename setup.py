#!/usr/bin/env python

"""
distutils/setuptools install script.
"""

import os
import re
import sys
import codecs

try:
    from setuptools import setup
    setup
except ImportError:
    from distutils.core import setup


here=os.path.abspath(os.path.dirname(__file__))


# Read the version number from a source file.
# Why read it, and not import?
# see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file=f.read()

    # The version line must have the form
    # __version__='ver'
    version_match=re.search(r"^__version__ = \(([^'\",]*),\s*([^'\",]*),\s*([^'\",]*).*\)",
                            version_file, re.M)
    if version_match:
        return "{}.{}.{}".format(version_match.group(1), version_match.group(2), version_match.group(3))
    raise RuntimeError("Unable to find version string.")

packages = [
    'boto3',
    'boto3.core',
    'boto3.sqs',
    'boto3.utils',
]

requires = [
    'botocore>=0.24.0',
    'six>=1.4.0',
    'jmespath>=0.1.0',
    'python-dateutil>=2.1',
    'bcdoc==0.12.2'
]

dependency_links = [
    'git+https://github.com/boto/bcdoc.git@develop#egg=bcdoc'
]

setup(
    name='boto3',
    version=find_version('boto3', '__init__.py'),
    description='Low-level, data-driven core of boto 3.',
    long_description=open('README.rst').read(),
    author='Amazon Web Services',
    author_email='garnaat@amazon.com',
    url='https://github.com/boto/boto3',
    scripts=[],
    packages=packages,
    package_data={
        'boto3': [
            'data/aws/resources/*.json',
        ]
    },
    include_package_data=True,
    install_requires=requires,
    dependency_links=dependency_links,
    license=open("LICENSE").read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
)
