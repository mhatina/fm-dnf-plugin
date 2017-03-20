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
#
# Written by Jan Kaluza
#            James Antill


"""
Command line interface fm class and related functions.
"""

from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import time
import fnmatch
import stat

import fm.exceptions
from fm.api_clients import APIClients
from fm.option_parser import OptionParser
from fm.module import Module
from fm.modules import Modules
from fm.config_file import ConfigFile

import json

class Cli(object):
    """ Class representing command line interface for controlling modules """

    def __init__(self, output = sys.stdout):
        """
        Creates new Cli class instance.

        :param file output: File to which the output is written.
        """

        #: File to which the output is written.
        self.output = output
        #: APIClient instance to query the remote API server.
        self.api = None
        #: OptionParser instance to handle command line arguments.
        self.optparser = OptionParser()
        #: Options set by command line.
        self.opts = None
        self.config_file = ConfigFile()

    def write(self, *args):
        """
        Writes arguments to the output file. Arguments are white-space
        separated in the output.

        :param list args: List of objects to write to output.
        """
        if len(args[0]) == 0:
            return

        print(" ".join(map(str, args)), file=self.output)

    def parse_args(self, args):
        self.opts, args = self.optparser.parse_known_args(args)
        self.config_file.load(self.opts.config)
        self.api = APIClients(self.config_file, self.opts)
        return args

    def run(self, opts):
        subcommand = ""
        args = self.parse_args(opts.arg)

        if opts.subcommand is not None:
            subcommand = self.opts.subcommand[0]

        try:
            arg = args[1]
        except (ValueError, IndexError):
            arg = None

        try:
            if subcommand == "help":
                self.print_help()
                return 0
            elif subcommand == "list":
                return self.list_modules()
            elif subcommand == "list-enabled":
                return self.list_enabled_modules()
            elif subcommand == "info":
                return self.info_modules(arg)
            elif subcommand == "summary":
                return self.summary_modules()
            elif subcommand == "search":
                return self.search_modules(self.opts)
            elif subcommand == "enable":
                return self.enable_module(arg, args)
            elif subcommand == "disable":
                return self.disable_module(arg)
            elif subcommand == "refresh":
                return self.refresh_cache()
            elif subcommand == "upgrade":
                return self.upgrade_modules(args)
            elif subcommand == "check-upgrade":
                return self.check_upgrade_modules(args)
            elif subcommand == "rebase":
                return self.rebase_module(arg, args)
            elif subcommand == "check-rebase":
                return self.check_rebase_modules(args)
            else:
                raise fm.exceptions.Error('Unknown subcommand {}.'.format(subcommand))
        except fm.exceptions.APICallError:
            if self.opts.verbose:
                self.write("Raw data received from the API server:\n",
                           '"""\n',
                           "{}\n".format(self.api.get_raw_data()),
                           '"""\n')
            raise

    def print_help(self):
        """
        Prints "help" message.
        """
        fn = sys.argv[0]
        if fn.find("dnf") != -1:
            fn += " module"
        self.write("{}: Fedora modularization command line interface. ".format(fn))
        self.write("")
        self.write("Commands:")
        self.write("    {} check-upgrade - Check for the availability of upgrade for enabled modules".format(fn))
        self.write("    {} enable <module-nvr> [profile, ...] - Enable the module and its dependencies.".format(fn))
        self.write("    {} disable <module> - Disable the module, depending modules and remove all module packages.".format(fn))
        self.write("    {} help - Show this help message.".format(fn))
        self.write("    {} info <module> - Show detail module information.".format(fn))
        self.write("    {} list - List all available modules.".format(fn))
        self.write("    {} list-enabled - List enabled modules.".format(fn))
        self.write("    {} rebase <module-nvr> - Rebase the module to particular version".format(fn))
        self.write("    {} refresh - Refresh the local modules cache".format(fn))
        self.write("    {} search <args> Search for a module using at least one of the following args:".format(fn))
        self.write("        {} --name <name> - Optional: Search for module by name".format(fn))
        self.write("        {} --version <inequality> <version> - Optional: Search for module by version".format(fn))
        self.write("        {} --release <inequality> <release> - Optional: Search for module by release".format(fn))
        self.write("        {} --requires <name> <version> - Optional: Search for module by requires.".format(fn))
        self.write("        {} --license <license name> - Optional: Search for module by module license.".format(fn))
        self.write("        {} --json <json text> - Optional: Search using json. (See `--json help` for more details.)".format(fn))
        self.write("    {} summary - Show modules statistics.".format(fn))
        self.write("    {} upgrade <module> - Upgrade the module to latest release".format(fn))
        self.write("")
        self.write("Options:")
        self.write(self.optparser.get_usage())

    def upload_module(self, local_path):
        self.api.upload(local_path)
        return 0

    def enable_module(self, arg, args):
        if arg is None:
            self.write("No argument")
            return 1

        profiles = args[2:]
        if len(profiles) == 0:
            profiles = ["default"]

        mods = self.api.list_modules()
        mods.enable(arg, profiles)
        return 0

    def disable_module(self, arg):
        """
        Handles "disable" command. Disables the module.

        :param string arg: Name of the module.
        :return: Error code, 0 on success.
        :rtype: int
        """
        if arg is None:
            self.write("No argument")
            return 1

        # We don't need to fetch the module here, .disable() needs
        # just module name...
        mods = Modules(self.config_file, self.opts, self.api)
        mods.load_enabled_modules()
        mods.disable(arg)
        return 0

    def info_modules(self, module):
        """
        Handles "info" command. Prints the full information about module.

        :param string module: Name of the module.
        :return: Error code, 0 on success.
        :rtype: int
        """
        if module is None:
            self.write("No argument")
            return 1

        mods = self.api.list_modules()
        self.write(mods.get_full_description(module))
        return 0

    def summary_modules(self):
        """
        Handles "summary" command. Prints modules statistics.

        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = self.api.list_modules()
        mods_count = 0
        for _mods in mods.values():
            mods_count += len(_mods)
        self.write("Modules: %u" % mods_count)
        return 0

    def list_modules(self):
        """
        Handles "list" command. Prints the short list of available modules.

        :param string arg: Keyword to find the module according to,
            or None for printing list of all modules.
        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = self.api.list_modules()
        self.write(mods.get_brief_description())
        return 0

    def refresh_cache(self):
        mods = self.api.list_modules(True)
        mods.refresh_cache()

    def list_enabled_modules(self):
        """
        Handles "list-enabled" command. Prints the list of enabled modules.

        :param string arg: Keyword to find the module according to,
            or None for printing list of all modules.
        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = Modules(self.config_file, self.opts, self.api)
        mods.load_enabled_modules(enabled_by_user=not self.opts.show_requirements)
        self.write(mods.get_brief_description())
        return 0

    def search_modules(self, args):
        """
        Handles "search" command. Search for the modules and prints the results.

        :param string args: Keywords to find the modules according to
        :return: Error code, 0 on success.
        :rtype: int
        """

        if not args._search_name or not args._search_requires or not args._search_license or not args.search_version or not args._search_json:
            self.write("No arguments")
            return 1

        mods = Modules(self.config_file, self.opts, self.api)
        mods.load_available_modules()

        if len(mods) == 0:
            mods = self.api.list_modules()

        arg_dict = dict()

        #If the json argument is used, then parse json and ignore the rest of the parsing
        if args._search_json:
            for argument in args:
                if args._search_name or args._search_requires or args._search_license or args.search_version:
                    self.write("The --json option cannot be combined with other options. See help for more details.")
                    return 1

            #Add a help option to describe the format for the --json arg
            if args._search_jso == "help":
                fn = sys.argv[0]
                if fn.find("dnf") != -1:
                    fn += " module"

                self.write("json code must be enclosed in single quotes ('') and entered in the following example format:")
                self.write("   '{\"name\": [\"httpd\"], \"version\": [\"==\", \"2.2.15\"]}'\n")
                self.write("Available fields are: name, release, version, requires, license \n")
                self.write("Note that each item in each field is written as a list, and multiple items may be added to each list, except in the case of \"version\" and \"release\", both of which require exactly 2 arguments.")
                return 1

            #Attempt to parse the json text
            try:
                tmp_dict = json.loads(args[2])

                for key in tmp_dict:
                    field = "_" + key
                    arg_dict[field] = tmp_dict[key]

            except ValueError:
                self.write("Invalid json format. See `--json help` for more details")
                return 1
        elif len(args) > 2:
            if args.search_version:
                if len(args.search_version) <= 1:
                    self.write("Insufficient number of arguments. --version requires the following 2 args: {inequality} {version number}")
                    return 1
                elif len(args.search_version) > 2:
                    self.write("Too many args. --version requires the following 2 args: {inequality} {version number}")
                    return 1
                elif args.search_version[0] not in ("==", "<=", ">=", "<", ">", "!="):
                      self.write("Invalid inequality. (Make sure inequality is enclosed in quotes -- e.g., '<') Valid inequalities: <, >, <=, >=, ==, !=")
                      return 1
                arg_dict["_version"] = args.search_version
            if args.search_requires:
                try:
                    tmp = args.search_version[0]
                    tmp = args.search_version[1]
                except IndexError:
                    self.write("Insufficient number of args. --requires needs exactly 2 args.")
                    return 1

                if len(arg_dict["_requires"]) > 2:
                    self.write("Too many args. --requires requires the following 2 args: {module name} {module version}")
                    return 1

                arg_dict["_requires"] = {args.search_version[0]: args.search_version[1]}
            if args.search_name:
                arg_dict["_name"] = args.search_name
            if args.search_license:
                arg_dict["_license"] = args.search_license
        else:
            self.write("Insufficient number of arguments.")
            return 1

        matching_mods = mods.search(arg_dict)
        self.write(matching_mods.get_brief_description())

        return 0

    def upgrade_modules(self, args):
        """
        Upgrades modules to latest available releases, but keeps the same
        modules' versions. For example "httpd-2.2.15-1" to "httpd-2.2.15-2".

        :param list mods: List of module names to update. If empty list is
            supplied, all modules are updated.
        :return: Error code, 0 on success
        :rtype: int
        """
        mods = self.api.list_modules()
        mods.upgrade(args[1:])
        return 0

    def check_upgrade_modules(self, args):
        """
        Prints list of modules for which the upgrade is available.
        """
        mods = self.api.list_modules()
        to_upgrade = mods.check_upgrade(args[1:])
        self.write(to_upgrade.get_brief_description())
        return 0

    def check_rebase_modules(self, args):
        """
        Prints list of modules for which the rebase is available.
        """
        mods = self.api.list_modules()
        to_upgrade = mods.check_rebase(args[1:])
        self.write(to_upgrade.get_brief_description())
        return 0

    def rebase_module(self, arg, args):
        profiles = args[2:]
        if len(profiles) == 0:
            profiles = ["default"]

        mods = self.api.list_modules()
        mods.rebase(arg, profiles)
        return 0
