Fedora modularization command line tool
=======================================

This is repository for Fedora modularization command line tool ("fm").

It is standalone "fm" command which is used query fm-metadata-service API
server to get metadata about available Fedora Modules.

In the future, this tool should be able to enable/disable modules and probably
also install them. The long term goals now are not set to stone yet.

Repository structure
--------------------

- bin - Directory with then main "fm" script installed to /usr/bin.
- docs - Documentation using the sphinx generator.
- fm - Module with the core "fm" functionality.
- plugins - DNF plugin implementing "dnf module" subcommand.
- tests - Unit-tests based on nosetests framework.

Documentation
-----------------

http://fm-dnf-plugin.readthedocs.org/

Fedora modularization command line tool and DNF plugin. It is used to query
fm-metadata-service and displays information about available modules.

It can be used as a standalone "fm" tool or as a DNF plugin adding "module"
subcommand to DNF.

Installation from source code
-----------------------------

You can install fm tool from source code using following commands:

::

	$ git clone https://pagure.io/fm-dnf-plugin.git
	$ cd fm-dnf-plugin
	$ cmake .
	$ sudo make install

Installation from RPM package
-----------------------------

We also provide RPM package with the latest version of fm tool. Since
we are in early stage in development, there is no stable fm release, so
the packages are rebuilt from time to time when we will it's worth doing
so.

To install the package, you can use following commands:

::

	$ sudo dnf copr enable @modularity/fm
	$ sudo dnf copr enable @modularity/modulemd
	$ sudo dnf copr enable @modularity/modulemd-resolver
	$ sudo dnf install python3-fm-dnf-plugin

Testing with example repository
-------------------------------

Create ``modules-repos.cfg`` file in the ``/etc/fm.modules.d`` directory:

::

    [modules-repos]
    name = Fedora modules repos
    url = http://dev.fed-mod.org/modularity/repos
    enabled = 1

Now you can try listing all available modules in the testing repository as root:

::

	# dnf module list
	apr      0.1-1       APR libraries module
	core     1.0-1       Core module
	httpd    2.2.15-1    Apache httpd webserver module
	httpd    2.2.15-2    Apache httpd webserver module
	httpd    2.4.18-1    Apache httpd webserver module

Showing detailed information about module
-----------------------------------------

To show the detailed information about module, run:

::

    # dnf module info httpd
    Name: httpd
    Summary: Apache httpd webserver
    Version: 2.2.15
    Description: Apache httpd webserver module for testing purposes.
    Profiles:
        - default:
            - httpd
        - docs:
            - httpd-manual
            - httpd

You can also see available profiles here with the list of RPMs this profile installs.

Enabling modules
----------------

To enable the module, you can run following:

::

    # dnf module enable httpd

This command enables the latest version of httpd module.

To enable httpd in particular version, you can include the version in the ``enable`` command:

::

    # dnf module enable httpd-2.2.15

Or you can even include the release:

::

    # dnf module enable httpd-2.2.15-1

These commands also installs the RPMs listed in the ``default`` profile. To choose different
profile, use the ``-p`` command line option:

::

    # dnf module enable httpd -p docs
    
Listing enabled modules
-----------------------

To list all enabled modules, simply run:

::

    # dnf module list-enabled
    apr      0.1-1       APR libraries module
    core     1.0-1       Core module
    httpd    2.4.18-1    Apache httpd webserver

Disabling modules
-----------------

To disable particular module and the modules depending on the module, simply run:

::

    # dnf module disable httpd

Searching for modules
---------------------

To search for the module, simply run:

::

    # dnf module search {options}

Available options are:

::

    --name
    --version
    --requires
    --license
    --json

- The ``--name`` option allows users to search by name
- The ``--version`` option allows users to search by version
- The ``--requires`` option allows users to search for modules which require a specific module
- The ``--license`` option allows users to search by module
- The ``--json`` option allows users to type in json text

The ``--version`` option require two arguments: ``{inequality} {number}``. For example,

::

    # dnf module search --version '==' 2.2.15
    # dnf module search --version '<=' 2.2.15
    # dnf module search --version "!=" 2.2.15

Available inequalities are: ``==, <, >, <=, >=, !=``


With the exception of the ``--json`` option, the available arguments can be used individually or combined together. For example:

::
    
    # dnf module search --name httpd
    # dnf module search --name httpd --version '==' 2.2.15
    # dnf module search --version '==' 2.2.15


Upgrading modules
-----------------

It is even possible to upgrade module to latest release using the ``upgrade`` command.
This command keeps the same version of the module.

To upgrade from ``httpd-2.2.15-1`` to latest ``httpd-2.2.15-2``, you can run:

::

    # dnf module upgrade httpd

Switching between major versions of module
------------------------------------------

To switch between the major versions of module, use the rebase command:

::

    # dnf module rebase httpd-2.4.18
