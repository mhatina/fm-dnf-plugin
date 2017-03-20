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


from __future__ import print_function
import dnf
import dnf.cli.output
import dnf.exceptions
import os
import sys

import modulemd
import fm.exceptions


from fm.api_client import URLAPIClient, APIClient
from fm.modules import Modules
from fm.repo_config_file import RepoConfigFile


class APIClients(APIClient):
    """
    Class managing multiple APIClients instances and merging their results
    together.
    """
    def __init__(self, config_file, opts):
        """
        Creates new APIClients instance.
        """
        APIClient.__init__(self)

        #: Main fm configuration file.
        self.cfg = config_file
        #: Command line options
        self.opts = opts
        #: List of APIClients.
        self.api_clients = {}

        self.create_api_clients()

    def create_api_client(self, repo_cfg, repo_name):
        """
        Creates new APIClient according to section in configuration file.

        :param ConfigParser cfg: Module repository configuration file.
        :param string section: Section in the configuration file describing the module.
        :return: New APIClient instance or None for disabled repositories.
        :rtype: APIClient or None
        :raises fm.exceptions.ConfigFileError: If configuration cannot be parsed.
        """
        # Check if this repository is enabled.
        if not repo_cfg.is_enabled(repo_name):
            return None

        # Check that we have 'url' arg in the config file.
        if not repo_cfg.has_option(repo_name, "url"):
            return None

        # Create and return proper APIClient subclass.
        return URLAPIClient(repo_cfg, repo_name, self.cfg, self.opts, self)

    def create_api_clients(self):
        """
        Creates APIClients instances according to configuration files in
        fm.modules_dir directory defined in the main fm configuration file.

        :raises fm.exceptions.ConfigFileError: If configuration cannot be parsed.
        """
        modules_dir = self.cfg.get_modules_dir()

        for cfg in os.listdir(modules_dir):
            cfg_path = os.path.join(modules_dir, cfg)
            repo_cfg = RepoConfigFile()
            repo_cfg.load(cfg_path)

            for repo_name in repo_cfg.sections():
                api_client = self.create_api_client(repo_cfg, repo_name)
                if not api_client:
                    continue

                self.api_clients[repo_name] = api_client

    def get_api_client(self, repo_name):
        """
        Returns the APIClient with particular repo_name.
        """
        if not repo_name in self.api_clients:
            return None
        return self.api_clients[repo_name]

    def list_modules(self, ignore_cache = False):
        """
        Lists the available modules.

        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        :raises fm.exceptions.APICallError: If the YAML cannot be retrieved or parsed.
        """
        mods = Modules(self.cfg, self.opts, self)
        mods.load_available_modules()
        if not ignore_cache and mods.is_cache_valid():
            return mods

        print("Modules cache expired, trying to refetch the modules list")

        mods = Modules(self.cfg, self.opts, self)
        for client in self.api_clients.values():
            mods.merge(client.list_modules())

        mods.remove_old_cached_modules()
        return mods

    def info_modules(self, arg):
        """
        Returns detail information about module.

        :param string arg: Name of the module for which the info is returned.
        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        :raises fm.exceptions.APICallError: If the YAML cannot be retrieved or parsed.
        """
        mods = Modules(self.cfg, self.opts, self)
        mods.load_available_modules()
        if arg in mods:
            if mods.is_cache_valid(arg):
                ret = Modules(self.cfg, self.opts, self)
                did_fetch = False
                for mod in mods[arg]:
                    if mod.fetch_module_metadata():
                        did_fetch = True
                    ret.add_module(mod)
                if did_fetch:
                    ret.refresh_cache()
                return ret
            else:
                print("Modules cache expired, trying to refetch the modules list")

        mods = Modules(self.cfg, self.opts, self)
        for client in self.api_clients.values():
            mods.merge(client.info_modules(arg))

        mods.remove_old_cached_modules()
        return mods


class DnfBase:
    def __init__(self):
        """
        Setup DNF - read all repos, and fill - sack.
        """
        # Todo - dnf.Base() should be replaced by dnf.cli.base available for
        # plugins commands.
        self.dnfbase = dnf.Base()
        # Todo - remove when dnf.cli.base is used - this is no API
        self.output = dnf.cli.output.Output(self.dnfbase, self.dnfbase.conf)
        self.repo_files = {'enabling': [], 'disabling': []}
        # if self.pluginbase - allow_erasing setting is used from dnf.conf
        self.allow_erasing = False
        self.pluginbase = False

    def _dnfsetup(self):
        if not self.dnfbase.sack:
            if self.pluginbase:
                self.dnfbase.repos.clear()
            self.dnfbase.read_all_repos()
            self.dnfbase.fill_sack()

    def _repo_id(self, reponame):
        return '_fm_' + reponame

    def repofiles_action(self, repo_files_action):
        if repo_files_action == 'roll_back':
            for repo_file in self.repo_files['enabling']:
                repo_file.remove()
            for repo_file in self.repo_files['disabling']:
                repo_file.create()
        if repo_files_action == 'disabling':
            for repo_file in self.repo_files['disabling']:
                repo_file.remove()

    def dnf_install(self, pkg_specs, module_name, repo_file, strict=True,
                    allow_erasing = False):
        """
        Mark packages given by pkg_spec from module repository for installation.
        @param pkg_specs: list of pkg_specs
        @param module_name - from it has to be installed:
        @param strict: dnf strict options
        """
        self.repo_files['enabling'].append(repo_file)
        if allow_erasing:
            self.allow_erasing = allow_erasing
        self._dnfsetup()
        errors = []
        for pkg_spec in pkg_specs:
            try:
                self.dnfbase.install(
                    pkg_spec, reponame=self._repo_id(module_name), strict=True)
            except dnf.exceptions.MarkingError as e:
                print(e)
                print('No match for argument: ' + pkg_spec)
                errors.append(e)
        if errors and strict:
            raise dnf.exceptions.MarkingError("Unable to find a match")

    def dnf_remove(self, module_name, repo_file, allow_erasing = False):
        """
        Mark all packages installed from module repository for installation.
        @param module_name: string - name of module
        @param repo_file: Object that will be deleted
        """
        self.repo_files['disabling'].append(repo_file)
        if allow_erasing:
            self.allow_erasing = allow_erasing

        self._dnfsetup()
        done = False

        # Remove all packages.
        try:
            self.dnfbase.remove('*', self._repo_id(module_name))
        except dnf.exceptions.MarkingError:
            print('No package installed from the repository.')
        else:
            done = True

        if not done:
            raise dnf.exceptions.Error('No packages marked for removal.')

    def dnf_upgrade(self, module_name, allow_erasing = False):
        """
        Upgrade all packages installed from module repository by packages from
        same repository
        @param module_name: string - name of module
        """
        if allow_erasing:
            self.allow_erasing = allow_erasing

        self._dnfsetup()
        done = False
        reponame = self._repo_id(module_name)
        pkg_specs = [pkg.name for pkg in self.dnfbase.sack.query().installed()
                     if pkg.from_repo == '@' + reponame]
        done = False
        for pkg_spec in pkg_specs:
            try:
                self.dnfbase.upgrade(pkg_spec, reponame)
            except dnf.exceptions.MarkingError:
                print('No match for argument: ' + pkg_spec)
            else:
                done = True
        if not done:
            raise dnf.exceptions.Error('No packages marked for upgrade.')

    def transaction_run(self):
        """
        Perform transaction for marked packages including dep-solving
        @param allow_erasing: DNF option
        """

        try:
            self.dnfbase.resolve(allow_erasing=self.allow_erasing)
        except dnf.exceptions.DepsolveError as e:
            print(e)
            self.repofiles_action('roll_back')
            sys.exit('Dependencies cannot be resolved.')
        print(self.output.list_transaction(self.dnfbase.transaction))
        try:
            self.dnfbase.download_packages(self.dnfbase.transaction.install_set)
        except dnf.exceptions.DownloadError as e:
            print(e)
            self.repofiles_action('roll_back')
            sys.exit('Required package cannot be downloaded.')
        # The request can finally be fulfilled.
        self.dnfbase.do_transaction()
        self.repofiles_action('disabling')


DNFBASE = DnfBase()
