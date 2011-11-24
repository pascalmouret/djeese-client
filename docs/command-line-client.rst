##########################
Djeese Command Line Client
##########################

Djeese offers a command line client to make certain tasks easier.


************
Requirements
************

The djeese command line client requires Python 2.5 or a higher version of the
2.x series of Python as well as the requests library (version 0.8 or higher).
The latter should be automatically installed when installing the djeese command
line client.

The djeese command line client is currently only supported on Linux and
Mac OS X, although it should also work on Windows. 


************
Installation
************

Make sure your system has Python installed and that it is available from your
command line.

Install pip by following the installation instructions on the `pip website`_.

Install the djeese command line client using ``pip install djeese`` (this might
require root privileges).


*****
Usage
*****

The djeese command line client can be called using the ``djeese`` command from
your command line after you successfully installed it.

Following options are available to all subcommands:

.. program:: djeese
.. option:: -v 1
.. option:: --verbosity 1

    Set the verbosity of the command. Available options: ``0``, ``1``, ``2``,
    ``3`` and ``4``. Higher values means more output.

.. option:: --help

    Shows help for the specified subcommand.


``djeese createapp``
====================

    Starts an interactive session to create Djeese Application Configuration
    file as described in :doc:`app-configuration`. This command requires
    internet access.


``djeese checkapp <filename>``
==============================

Validates the Djeese Application Configuration in ``<filepath>``.


``djeese uploadapp <setup.py> <filename>``
==========================================

Builds and uploads an application to djeese. The ``<setup.py>`` is the file to
install your application. ``<filepath>`` is the path to your Djeese Application
Configuration file.

.. _pip website: http://www.pip-installer.org/en/latest/installing.html
