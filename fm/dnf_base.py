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
import sys


class DnfBase:
    def __init__(self):
        """
        Setup DNF - read all repos, and fill - sack.
        """
        # Todo - dnf.Base() should be replaced by dnf.cli.base available for
        # plugins commands.
        self.base = dnf.Base()
        # Todo - remove when dnf.cli.base is used - this is no API
        self.output = dnf.cli.output.Output(self.base, self.base.conf)
        self.repo_files = {'enabling': [], 'disabling': []}
        # if self.pluginbase - allow_erasing setting is used from dnf.conf
        self.allow_erasing = False
        self.pluginbase = False

    def _dnfsetup(self):
        if not self.base.sack:
            if self.pluginbase:
                self.base.repos.clear()
            self.base.read_all_repos()
            self.base.fill_sack()

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
                self.base.install(
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
            self.base.remove('*', self._repo_id(module_name))
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
        pkg_specs = [pkg.name for pkg in self.base.sack.query().installed()
                     if pkg.from_repo == '@' + reponame]
        done = False
        for pkg_spec in pkg_specs:
            try:
                self.base.upgrade(pkg_spec, reponame)
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
            self.base.resolve(allow_erasing=self.allow_erasing)
        except dnf.exceptions.DepsolveError as e:
            print(e)
            self.repofiles_action('roll_back')
            sys.exit('Dependencies cannot be resolved.')
        print(self.output.list_transaction(self.base.transaction))
        try:
            self.base.download_packages(self.base.transaction.install_set)
        except dnf.exceptions.DownloadError as e:
            print(e)
            self.repofiles_action('roll_back')
            sys.exit('Required package cannot be downloaded.')
        # The request can finally be fulfilled.
        self.base.do_transaction()
        self.repofiles_action('disabling')
