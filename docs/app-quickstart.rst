######################
Application Quickstart
######################

This quickstart tutorial should teach you all the basics about writing a django
CMS plugin and publishing it on the djeese platform.


*************
Prerequisites
*************

You need to have a computer with access to the internet, `Python`_ 2.6 or a
higher 2.x version installed and a text editor. This guide was tested on Ubuntu
11.10, but should work on other Unix based systems. 


***************************
Setting up your environment
***************************

First, you need to make sure `Python`_ is installed correctly:

.. code-block:: bash

    python --version
    
This should print "Python 2.x.y" where "x" is at least 6. If your system cannot
find ``python``, install it from `python.org`_.

Next, install `pip`_ follwing their `installation instructions`_.

Now, install the `djeese`_ command line client using:

.. code-block:: bash

    sudo pip install djeese
    

*******************
Writing your plugin
*******************

In this tutorial, we'll write a plugin that will greet the user on the page.
The plugin will be called ``cmsplugin-hello``, so create an empty folder called
``cmsplugin-hello`` somewhere in your filesystem. All file paths from here are
relative to that directory.


Basics
======

A django CMS plugin consists at least of the following files:

* ``setup.py``
* ``MANIFEST.in``
* ``README.rst``
* ``LICENSE.txt``
* ``<plugin-name>/__init__.py``
* ``<plugin-name>/models.py``
* ``<plugin-name>/cms_plugins.py``

For the djeese platform the ``djeese.ini`` file is also required, and one or
several templates in ``<plugin-name>/templates/``.

For this simple example, we don't need models, but the file is still needed.

So go ahead and create the following (empty) files:

* ``cmsplugin_hello/__init__.py``
* ``cmsplugin_hello/models.py``
* ``cmsplugin_hello/cms_plugins.py``

Coding the logic
================

Open ``cmsplugin_hello/cms_plugins.py`` in your favorite text editor. Write the
following contents:

.. code-block:: python
    :linenos:
    
    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    
    class HelloPlugin(CMSPluginBase):
        name = 'Hello Plugin'
        render_template = 'cmsplugin_hello/hello_plugin.html'
        
        def render(self, context, instance, placeholder):
            return context
    
    plugin_pool.register_plugin(HelloPlugin)

CMS plugins are Python classes subclassing :class:`cms.plugin_base.CMSPluginBase`
that get registered with :meth:`cms.plugin_pool.plugin_pool.register_plugin`.

The minimum a CMS plugin must provide is:

* An attribute called ``name`` which is a string defining the verbose name of
  this plugin.
* An attribute called ``render_template`` which is the template name to render
  this plugin as a string. The name should never start with a slash and it is
  good practice to put them in a folder named after the plugin.
* A method called ``render`` accepting the arguments ``context``, ``instance``
  and ``placeholder`` which returns a dictionary or a Django template context
  instance.
  
In the example above, we define a plugin with the verbose name ``'Hello Plugin'``
which will render the ``'cmsplugin_hello/hello_plugin.html'`` template. In the
:meth:`render` method we don't do anything special and just pass the inherited
context to the template.


Writing the template
====================

We want the plugin to say ``'Hello <strong>Guest</strong>'`` to anonymous users
and greet logged in users with ``'Hello <strong>username</strong>`` replacing
``username`` with the actual user name of the user. For this purpose, open
``cmsplugin_hello/templates/cmsplugin_hello/hello_plugin.html`` in your text
editor and write the following contents:

.. code-block:: html+django
    :linenos:
    
    {% if request.user.is_authenticated %}
        Hello <strong>{{ request.user.username }}</strong>
    {% else %}
        Hello <strong>Guest</strong>
    {% endif %}

Plugin templates are written using the `Django template language`_ and in this
example we check if the user is authenticated, and if so, greet them with their
user name, otherwise just greet them as guests.

Now you have all the basic pieces for your plugin.


Packaging
=========


Setup Script
------------

You need to package your plugin using the standard Python packaging tools. For
this purpose, open the ``setup.py`` file in your text editor and write the 
following contents, replacing all the values in ``<>`` with sensible values:

.. code-block:: python

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    from setuptools import setup
    
    
    INSTALL_REQUIRES = [
        'django-cms>=2.2',
    ]
    
    CLASSIFIERS = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ]
    
    setup(
        name='cmsplugin-hello',
        version='1.0',
        description='Hello Plugin for django CMS',
        author='<yourname here>',
        author_email='<your email here>',
        packages=['cmpslugin_hello'],
        install_requires=INSTALL_REQUIRES,
        license='BSD License',
        platforms=['OS Independent'],
        classifiers=CLASSIFIERS,
        long_description=open('README.rst').read(),
        include_package_data=True,
        zip_safe=False
    )
    

Packaging Python applications correctly is arguably the hardest part about
distributing Python code. So let's see what we did here.

The ``setup.py`` file is the script that gets run when a Python package is
installed. In this example, we use `setuptools`_ to help us with that by 
calling it's :func:`setup` function. That function can take many arguments, but
we will only use the most important ones here:

* ``name`` is the (unique) name for this package. For CMS plugins, the
  convention is to prefix the name with ``cmsplugin-``.
* ``version`` is the version string for this release. Note that this is not
  necessarily the same version you define in the Djeese Application
  Configuration later in this tutorial. You should use the versioning schema
  defined in :pep:`386`.
* ``description`` is a short one line description of what your package is.
* ``author`` and ``author_email`` is you. This way people can contact you for
  praise and correctly attribute authorship.
* ``packages`` is a list of Python modules this package contains. A Python
  module is basically a folder with an ``__init__.py`` file. In our case, we
  only have ``cmsplugin_hello`` but bigger packages might have a whole list of
  modules here.
* ``license`` defines what license this code is released under, in this example
  we use the BSD license, which is the most common open source license for
  Django applications. Note that the djeese platform does not require you to
  use an open source license, but you must specify a license.
* ``platforms`` can be a list of platforms (operating systems) that are
  supported by this package. Since Python is very good in cross platform
  support, for most packages ``OS Independent`` will work.
* ``classifiers`` is a list of classifiers describing your package in a machine
  readable way. A full list of supported classifiers can be found on `pypi`_.
* ``long_description`` is the a long description for your package. In this
  example we just read out the contents of the ``README.rst`` file.
* ``include_package_data`` tells setuptools to also include non-python files
  in the packages. Specifically templates in our case.
* ``zip_safe`` should always be ``False`` for Django packages, since not all
  Django projects are configured to support loading of templates from zip files.


Manifest
--------

Since we include non-python data in our package, we need to provide a
``MANIFEST.in`` file containing information about what other data to include.

Open ``MANIFEST.in`` in your text editor and write:

.. code-block:: text

    include LICENSE.txt
    include README.rst
    recursive-include cmsplugin_hello/templates *
    recursive-exclude * *.pyc

This includes the ``LICENSE.txt`` and ``README.rst`` files as well as our
templates in the distribution package. 


License & Readme
----------------

All packages should also contain a ``LICENSE.txt`` file with the full license
text for your application and a ``README.rst`` file containing a long
description and documentation about your package. Create those two files now.


Make your app djeese ready
==========================

For your application to work on the djeese platform, you have to provide a 
Djeese Application Configuration. The easiest way to create one is to run
``djeese createapp``. This command line tool will ask you a series of questions
and create the configuration file for you.

.. note:: Since app names on the djeese platform must be unqiue, you probably
          should use a more unique name when prompted. For example, append your
          djeese username. Otherwise the upload will fail.


Upload your app to djeese
=========================

Run the following command:

.. code-block:: bash

    djeese uploadapp setup.py djeese.ini


.. _python.org: http://python.org/download/releases/2.7.2/
.. _Python: http://www.python.org
.. _pip: http://www.pip-installer.org/ 
.. _installation instructions: http://www.pip-installer.org/en/latest/installing.html
.. _djeese: https://github.com/djeese/djeese-client
.. _open source license: http://www.opensource.org/licenses
.. _Django template language: https://docs.djangoproject.com/en/dev/ref/templates/
.. _setuptools: http://pypi.python.org/pypi/setuptools
.. _pypi: http://pypi.python.org/pypi?%3Aaction=list_classifiers
