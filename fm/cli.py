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

from __future__ import absolute_import
from __future__ import print_function

import json
import sys

import fm.exceptions
from fm.config_file import ConfigFile, ModuleSection
from fm.modules import Modules
from fm.option_parser import OptionParser


class Cli(object):
    """ Class representing command line interface for controlling modules """

    def __init__(self, output = sys.stdout):
        """
        Creates new Cli class instance.

        :param file output: File to which the output is written.
        """

        #: File to which the output is written.
        self.output = output
        #: OptionParser instance to handle command line arguments.
        self.optparser = OptionParser()
        #: Options set by command line.
        self.opts = None
        self.config_file = ConfigFile()

    def write(self, *args):
        if len(args[0]) == 0:
            return

        print("".join(map(str, args)), file=self.output)

    def parse_args(self, args):
        self.opts, args = self.optparser.parse_known_args(args)
        self.config_file.load()
        return args

    def run(self, opts):
        subcommand = ""
        args = self.parse_args(opts.arg)

        if opts.subcommand is not None:
            subcommand = opts.subcommand[0]

        try:
            arg = args[0]
        except (ValueError, IndexError):
            arg = None

        try:
            if subcommand == "help":
                self.print_help()
                return 0
            elif subcommand == "list":
                return self.list_modules()
            elif subcommand == "list-installed":
                return self.list_installed_modules()
            elif subcommand == "info":
                return self.info_modules(arg)
            elif subcommand == "install":
                return self.install_module(arg)
            elif subcommand == "summary":
                return self.summary_modules()
            elif subcommand == "search":
                return self.search_modules(self.opts)
            elif subcommand == "refresh":
                return self.refresh_cache()
            else:
                raise fm.exceptions.Error('Unknown subcommand {}.'.format(subcommand))
        except fm.exceptions.APICallError:
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
        self.write("    {} help - Show this help message.".format(fn))
        self.write("    {} info <module> - Show detail module information.".format(fn))
        self.write("    {} list - List all available modules.".format(fn))
        self.write("    {} list-installed - List installed modules.".format(fn))
        self.write("    {} refresh - Refresh the local modules cache".format(fn))
        self.write("    {} search <args> Search for a module using at least one of the following args:".format(fn))
        self.write("        {} search --name <name> - Optional: Search for module by name".format(fn))
        self.write("        {} search --version <inequality> <version> - Optional: Search for module by version".format(fn))
        self.write("        {} search --release <inequality> <release> - Optional: Search for module by release".format(fn))
        self.write("        {} search --requires <name> <version> - Optional: Search for module by requires.".format(fn))
        self.write("        {} search --license <license name> - Optional: Search for module by module license.".format(fn))
        self.write("        {} search --json <json text> - Optional: Search using json. (See `--json help` for more details.)".format(fn))
        self.write("    {} summary - Show modules statistics.".format(fn))
        self.write("")
        self.write("Options:")
        self.write(self.optparser.get_usage())

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

        mods = self.get_modules()
        self.write(mods.get_full_description(module))
        return 0

    def install_module(self, module):
        if module is None:
            self.write("No argument")
            return 1

        modules = Modules(self.config_file, self.opts)
        modules.load_modules()
        module_metadata = modules.get_modules(module)

        if module_metadata is None:
            self.write("No such module: {}".format(module))
            return 1
        module_metadata = module_metadata[0]

        self.enable_only_installed_module(module_metadata.repo)
        profiles = self.get_profiles_to_install()
        installed = self.install_profiles(module_metadata, profiles)
        section = ModuleSection(module_metadata.name,
                                "true",
                                str(module_metadata.version),
                                installed)
        self.config_file.update_module(section)

    @staticmethod
    def enable_only_installed_module(module_metadata):
        for repo in fm.dnfbase.base.repos.iter_enabled():
            repo.disable()
        module_metadata.enable()

    def get_profiles_to_install(self):
        profiles = ["default"]
        input_profile = self.get_profiles_from_user()
        if len(input_profile) is not 0:
            profiles = input_profile.split(",")
        return profiles

    @staticmethod
    def get_profiles_from_user():
        message = "What profiles do you want to install? (default) "
        try:
            input_profile = raw_input(message)
        except NameError:
            input_profile = input(message)
        return input_profile

    def install_profiles(self, module_metadata, profiles):
        no_profile_found = True

        installed_profiles = []
        for profile_name in profiles:
            if profile_name not in module_metadata.profiles.keys():
                self.write("No such profile: {}".format(profile_name))
                continue

            no_profile_found = False

            profile = module_metadata.profiles[profile_name]
            if self.install_packages(module_metadata, profile):
                installed_profiles.append(profile_name)

        if no_profile_found:
            self.write("Possible profiles: {}".format(list(module_metadata.profiles)))
        else:
            return installed_profiles

    @staticmethod
    def install_packages(module_metadata, profile):
        base = fm.dnfbase.base
        for repo in base.repos.iter_enabled():
            repo.disable()
        module_metadata.repo.enable()
        base.fill_sack()

        atleast_one_installed = False
        for rpm in profile.rpms:
            if base.install(rpm):
                atleast_one_installed = True

        return atleast_one_installed

    def summary_modules(self):
        """
        Handles "summary" command. Prints modules statistics.

        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = self.get_modules()
        self.write("Modules: {}".format(len(mods.values())))
        return 0

    def get_modules(self):
        mods = Modules(self.config_file, self.opts)
        mods.load_modules()
        return mods

    def list_modules(self):
        """
        Handles "list" command. Prints the short list of available modules.

        :param string arg: Keyword to find the module according to,
            or None for printing list of all modules.
        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = self.get_modules()
        self.write(mods.get_brief_description(False))
        return 0

    @staticmethod
    def refresh_cache():
        base = fm.dnfbase.base
        for module in base.repos.iter_module():
            module.enable()
        base.update_cache()

    def list_installed_modules(self):
        """
        Handles "list-enabled" command. Prints the list of enabled modules.

        :param string arg: Keyword to find the module according to,
            or None for printing list of all modules.
        :return: Error code, 0 on success.
        :rtype: int
        """
        mods = Modules(self.config_file, self.opts)
        mods.load_modules()
        self.write(mods.get_brief_description(True))
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

        mods = Modules(self.config_file, self.opts)
        mods.load_modules()

        if len(mods) == 0:
            mods = self.get_modules()

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
