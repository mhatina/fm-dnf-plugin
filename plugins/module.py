# supplies the 'module' command.
#
# Copyright (C) 2014-2016  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

"""
Fedora modularization DNF plugin is used to query fm-metadata-service and displays information about available modules.

Usage
-----

List all modules:

::

	dnf module list

Search for modules:

::

	dnf module search <module>

API documentation
-----------------

.. toctree::
   :maxdepth: 2

   module

"""

from __future__ import print_function

import sys
import traceback

import dnf
import dnf.cli
from dnf.i18n import ucd
from dnf.pycomp import PY3
from dnfpluginscore import _, logger

import fm.dnf_base
import fm.exceptions
from fm.cli import Cli
from fm.modules import Modules

YES = set([_('yes'), _('y')])
NO = set([_('no'), _('n'), ''])

# compatibility with Py2 and Py3 - rename raw_input() to input() on Py2
try:
    input = raw_input
except NameError:
    pass
if PY3:
    pass
else:
    pass


class Module(dnf.Plugin):
    """DNF plugin supplying the 'module' subcommand."""

    name = 'module'

    def __init__(self, base, cli):
        """Initialize the plugin instance."""
        super(Module, self).__init__(base, cli)
        if cli is not None:
            cli.register_command(ModuleCommand)
        self.base = base
        self.cli = cli


class ModuleCommand(dnf.cli.Command):
    """ Module plugin for DNF """

    #: Base URL for fm-metadata-service API.
    api_url = "https://copr.fedoraproject.org"
    #: DNF alias.
    aliases = ("module",)
    #: Summary describing this DNF plugin.
    summary = _("Interact Fedora Modules.")
    #: Basic usage of this DNF plugin.
    usage = _("""
  list
  search <module>

  Examples:
  module list
  module search httpd
    """)

    @staticmethod
    def set_argparser(parser):
        parser.add_argument('subcommand', nargs=1,
                            choices=['help', 'list', 'list-installed',
                                     'info', 'summary', 'search',
                                     'refresh', 'install'])
        parser.add_argument('arg', nargs='*')

        parser.add_argument('--name', dest='_search_name',
                             action='append', default=[],
                             help=_("search for module by name"))
        parser.add_argument('--requires', dest='_search_requires',
                             action='append', default=[],
                             help=_("Search for module by requires"))
        parser.add_argument('--license', dest='_search_license',
                             action='append', default=[],
                             help=_("Search for module by module license"))
        parser.add_argument('--module-version', dest='search_version',
                            action='append', default=[],
                            help=_("search for module by version"))
        parser.add_argument('--json', dest='_search_json',
                             action='append', default=[],
                             help=_("Search using json (See `--json help` for more details.)"))

    def configure(self):
        self._setup_resolving()

    def _setup_resolving(self):
        demands = self.cli.demands
        demands.resolving = False

    def run(self):
        fm.dnfbase.base = self.base
        fm.dnfbase.pluginbase = True

        try:
            Cli().run(self.opts)
        except fm.exceptions.Error as err:
            raise dnf.exceptions.Error(err)
        except Exception as e:
            print(e)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)

