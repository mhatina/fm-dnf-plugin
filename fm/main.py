#! /usr/bin/python
# Copyright (C) 2012-2016  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
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

	$ sudo dnf copr enable jkaluza/fm 

If you want to try also the DNF plugin, install also:

::

	$ sudo dnf install fm python3-fm-dnf-plugin

Usage
-----

List all modules:

::

	fm list
	dn module list

Show info about single module:

::

	fm info <module>
	dnf module info <module>

"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import os
import os.path

from fm.cli import Cli
import fm.exceptions

def main(args):
    cli = Cli()
    return cli.run(args)

def user_main(args, exit_code=False):
    try:
        errcode = main(args)
    except fm.exceptions.Error as err:
        print("Error:", err)
        errcode = 1
    if exit_code:
        sys.exit(errcode)
    return errcode

if __name__ == "__main__":
    user_main(sys.argv[1:], exit_code=True)
