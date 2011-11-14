#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
from djeese import __version__


INSTALL_REQUIRES = [
    'requests',
]
try:
    import json
except ImportError:
    INSTALL_REQUIRES.append('simplejson')

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development',
]

setup(
    name='djeese',
    version=__version__,
    description='The command-line client for the djee.se service',
    author='The djee.se Team',
    author_email='say@djee.se',
    url='http://djeese.com/',
    packages=['djeese', 'djeese.commands'],
    license='LICENSE.txt',
    platforms=['OS Independent'],
    install_requires=INSTALL_REQUIRES,
    entry_points="""
    [console_scripts]
    djeese = djeese:main
    """,
)
