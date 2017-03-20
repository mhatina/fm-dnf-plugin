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
from dnf.pycomp import PY3
from subprocess import call
from dnfpluginscore import _, logger
from dnf.i18n import ucd
import dnfpluginscore

import dnf
import dnf.cli
import glob
import json
import os
import platform
import shutil
import stat
from fm.cli import Cli
from fm.modules import Modules
import fm.exceptions
import fm.api_clients

import sys
import traceback

YES = set([_('yes'), _('y')])
NO = set([_('no'), _('n'), ''])

# compatibility with Py2 and Py3 - rename raw_input() to input() on Py2
try:
    input = raw_input
except NameError:
    pass
if PY3:
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser

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

    def sack(self):
        if not self.cli.demands.resolving or self.cli.base.basecmd in ("remove", "reinstall"):
            return

        # exclude packages installed from modules
        # these packages will be marked for installation
        # which could prevent them from upgrade and downgrade
        # to prevent "conflicting job" error it's not applied
        # to "remove" and "reinstall" commands
        module_repos = []
        cli = Cli()
        cli.parse_args([])
        mods = Modules(cli.config_file, cli.opts, cli.api)
        mods.load_enabled_modules()
        for _mods in mods.values():
            for mod in _mods:
                repo_name = mod.repo_file.get_repo_name()
                if not repo_name in module_repos:
                    module_repos.append("@" + repo_name)
        module_pkgs = self.base.sack.query().installed()
        installed_module_pkgs = \
            (p for p in module_pkgs if p.from_repo in module_repos)
        for pkg in installed_module_pkgs:
            try:  # dnf-1.1.9 to prevent warning message
                self.base._goal.install(pkg)
            except AttributeError:
                self.base.goal.install(pkg)


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
                            choices=['help', 'list', 'list-enabled',
                                     'info', 'summary', 'search',
                                     "enable", "disable", "refresh",
                                     "upgrade", "check-upgrade",
                                     "rebase", "check-rebase"])
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

    def run_transaction(self):
        """Perform the depsolve, download and RPM transaction stage."""
        # Solve problem with incorrect module repo file committing
        if self.base.sack:
            if self.base.transaction is None:
                self.base.resolve(self.cli.demands.allow_erasing)
                logger.info(_('Dependencies resolved.'))

            self.base._plugins.run_resolved()

            # Run the transaction
            displays = []
            if self.cli.demands.transaction_display is not None:
                displays.append(self.cli.demands.transaction_display)
            try:
                self.base.do_transaction(display=displays)
            except dnf.cli.CliError as exc:
                logger.error(ucd(exc))
                fm.api_clients.DNFBASE.repofiles_action('roll_back')
                return 1
            except dnf.exceptions.TransactionCheckError as err:
                fm.api_clients.DNFBASE.repofiles_action('roll_back')
                for msg in self.cli.command.get_error_output(err):
                    logger.critical(msg)
            except IOError as e:
                fm.api_clients.DNFBASE.repofiles_action('roll_back')
                raise e
            else:
                self.base._plugins.run_transaction()
                logger.info(_('Complete!'))
            fm.api_clients.DNFBASE.repofiles_action('disabling')
        return 0

    def run(self):
        """
        Executes subcommand passed to 'dnf' command.

        :param list extcmds: list List of subcommands.
        """
        fm.api_clients.DNFBASE.dnfbase = self.base
        fm.api_clients.DNFBASE.pluginbase = True

        try:
            Cli().run(self.opts)
        except fm.exceptions.Error as err:
            raise dnf.exceptions.Error(err)
        except Exception as e:
            print(e)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_tb(tb)

