################################
Djeese Application Configuration
################################

Applications for the Djeese Application Store must provide a configuration file
describing the properties and settings of an application.


*************************
Configuration File Format
*************************

Djeese Application Configurations are written in the INI file format as
understood by Python's `ConfigParser`_ module. While not required we recommend
you use the ``.ini`` extension for those files.

.. note::

    We decided to use file-based configurations over a web form so you can use
    your favorite version control system to version the configurations if you
    want to. This is optional of course. Further it keeps some options open for
    our command line tool in the future.


The Djeese Application Configuration file must have an ``app`` section and can
optionally have a ``templates`` section as well as a section for each setting
defined in the ``settings`` option in the ``app`` section.


The ``app`` Section
===================

The ``app`` section is the main (and only required) section in your Djeese
Application Configuration file. It has following **required** options:

* ``name``: The (unique) verbose name of your application.
* ``packagename``: The package name of your application.
* ``version``: The version of your application this configuration file describes.
* ``installed-apps``: A list of application names this application needs to
                      have in Django's ``INSTALLED_APPS`` setting.
* ``description``: A description of your application. May be multiple lines.
* ``license``: The license type of this application (BSD, MIT, proprietary, ...).
* ``license-text``: A (accessible) URL to the full license text of this application.
* ``url``: The URL to your applications project page.


It may further have following **optional** options:

* ``settings``: A list of settings this application exposes. The names given
                here do not have to be the actual setting names, but are merely
                references to a section with the same name in this file.
* ``author``: The name of the author of this application.
* ``author-url``: The URL to the authors website.
* ``translation-url``: Link to the translation page for this project, for
                       example the transifex page.


The ``templates`` section
=========================

The ``templates`` section defines templates that should be editable through
djeese by the users. For CMS Plugins this should include the template that gets
rendered by the plugin. Admin templates can and probably should be omitted.

The keys to this section are the template paths as used by Django's template
system. The values are a link to the template source code.


The setting sections
====================

For each setting defined in the ``settings`` option of the ``app`` section, you
must create a section with the same name. This section has following
**required** options:

* ``name``: The name of this setting. This is the name used in Python.
* ``verbose-name``: The verbose name of this setting as used on the djeese site
                    when the user is prompted to configure this setting.
* ``type``: The type of this setting. Available values are: :describe:`string`,
            :describe:`stringlist`, :describe:`stringtuplelist` and
            :describe:`boolean`. 

It may also include following **optional** options:

* ``default``: The default value for this setting. Only available for the
               ``string`` type at the moment.
* ``required``: If set to ``false`` makes this setting optional. By default all
                settings defined are required.
* ``editable``: If set to ``false`` makes this setting non-editable. This
                requires the setting to have a ``default`` set. This option
                should be avoided if possible. 

.. _setting-types:

Setting types
-------------

.. describe:: string

    A simple string. For example ``"hello world"``.

.. describe:: stringlist

    A list of strings. For example ``['hello', 'world']``.

.. describe:: stringtuplelist

    A list of tuples of strings. For example ``[('en', 'English')]``.

.. describe:: boolean

    A boolean flag (``True`` or ``False``).


An Example
==========

This is an example Djeese Application Configuration for the `CMSPlugin Disqus`_.

.. code-block:: ini

    [app]
    name = CMSPlugin disqus
    packagename = cmsplugin-disqus
    url = https://github.com/djeese/cmsplugin-disqus
    author = Djeese Factory GmbH
    author-url = https://github.com/djeese
    installed-apps = 
        cmsplugin_disqus
    version = 1.0
    description = Disqus plugin for django CMS
    license = BSD
    license-text = https://raw.github.com/djeese/cmsplugin-disqus/master/LICENSE.txt
    translation-url = https://raw.github.com/djeese/cmsplugin-disqus/master/LICENSE.txt
    settings = 
        shortname
    
    [shortname]
    name = DISQUS_SHORTNAME
    verbose-name = Disqus Site Shortname
    type = string
    required = true
    
    [templates]
    cmsplugin_disqus/disqus_plugin.html = https://raw.github.com/djeese/cmsplugin-disqus/master/cmsplugin_disqus/templates/cmsplugin_disqus/disqus_plugin.html


.. _ConfigParser: http://docs.python.org/library/configparser.html
.. _CMSPlugin Disqus: https://github.com/djeese/cmsplugin-disqus
