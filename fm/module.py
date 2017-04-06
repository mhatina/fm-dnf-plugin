# optparse.py
# CLI options parser.
#
# Copyright (C) 2016  Red Hat, Inc.
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

import argparse
import sys
import re
import os
import stat
import fm.exceptions
import dnf

from fm.repo_file import RepoFile
import fm.dnf_base

from subprocess import *


class Module(object):
    """
    Class representing Fedora Module.
    """

    def __init__(self, api, name, url = None, mmd = None, root = "/"):
        """
        Creates new Fedora Module representation.

        :param string name: Name of the module.
        :param modulemd.ModuleMetadata: Module metadata if available.
        """
        # API Client used to obtain this module.
        self.api = api
        #: Name of the module.
        self.name = name
        #: ModuleMetadata instance
        self.mmd = mmd
        #: URL with module's repository
        self.url = url

        self.repo_file = RepoFile(name, url, root)

    def get_nvr(self):
        """
        Returns NVR ("$name-$version-$release) of this module.
        """
        return self.name + "-" + self.mmd.version + "-" + self.mmd.release

    def get_metadata_expire(self):
        """
        Returns configured metadata expiration time for this module.
        """
        if not self.api:
            return -1

        return self.api.get_metadata_expire()

    def _install_profile_rpms(self, profile_names):
        """
        Installs RPMs defined in the Module's profile `profile_name`.
        """

        if not self.mmd:
            return

        rpms = []
        for profile_name in profile_names:
            if not profile_name in self.mmd.profiles:
                continue

            profile = self.mmd.profiles[profile_name]
            if len(profile.rpms) == 0:
                continue

            rpms += profile.rpms

            fm.dnf_base.DNFBASE.dnf_install(rpms, self.name,
                                            self.repo_file,
                                            strict=True,
                                            allow_erasing = True)

    def fetch_module_metadata(self):
        """
        Fetches the full metadata using the API Client associated with this
        module. Does nothing when data has been fetched already.
        """
        if not self.mmd or "_fm_need_refetch" in self.mmd.xmd:
            self.mmd = self.api.get_module_metadata(self.url)
            return True
        return False

    def enable(self, profiles = ["default"], call_dnf = True):
        """
        Enables the module - downloads the repository file to
        $root/etc/yum.repos.d and installs all default packages for module.

        :param string root: Full path to root file-system.
        :param bool call_dnf: True if DNF should be called.
        :raises fm.exceptions.Error: If DNF exits with an error code.
        """
        self.repo_file.create()

        # Install the packages according to chosen profile.
        if call_dnf:
            self.fetch_module_metadata()
            try:
                self._install_profile_rpms(profiles)
            except fm.exceptions.Error as err:
                self.repo_file.remove()
                raise

    def upgrade(self, call_dnf = True):
        """
        Upgrades the packages provided by module to new release.
        """
        if call_dnf:
            fm.dnf_base.DNFBASE.dnf_upgrade(self.name)

    def disable(self, call_dnf = True):
        """
        Disables the module - removes repository file from $root/etc/yum.respo.d
        and uninstalls all the packages installed from that repository.

        :param string root: Full path to root file-system.
        :param bool call_dnf: True if DNF should be called.
        :raises fm.exceptions.Error: If DNF exits with an error code.
        """
        if call_dnf:
            try:
                fm.dnf_base.DNFBASE.dnf_remove(self.name, self.repo_file)
            except dnf.exceptions.Error as err:
                if str(err) != "No packages marked for removal.":
                    raise
        else:
            self.repo_file.remove()

    def is_enabled(self):
        """
        Returns True if the module is enabled.

        :return: True if the module is enabled.
        :rtype: bool
        """
        return self.repo_file.is_created()

    def get_brief_description(self):
        """
        Returns brief (short) description of the module.
        :return: Description of the module.
        :rtype: string
        """
        ret = "Name: " + self.name + "\n"
        if self.mmd:
            ret += "  Summary: " + self.mmd.summary + "\n"
            ret += "  Version: " + self.mmd.version + "\n"

        return ret

    def get_full_description(self):
        """
        Returns the full (long) description of the module.
        :return: Description of the module.
        :rtype: string
        """
        ret = "Name: " + self.name + "\n"
        if self.mmd:
            ret += "  Summary: " + self.mmd.summary + "\n"
            ret += "  Version: " + self.mmd.version + "\n"
            ret += "  Release: " + self.mmd.release + "\n"
            ret += "  Description: " + self.mmd.description + "\n"

            if self.mmd.profiles and len(self.mmd.profiles) != 0:
                ret += "  Profiles:\n"
                for profile in sorted(self.mmd.profiles.keys()):
                    if profile == "default":
                        desc = "Default list of packages."
                    else:
                        desc = self.mmd.profiles[profile].description

                    if len(desc) == 0:
                        desc = profile + " profile."

                    ret += "    - " + profile + ": " + desc + "\n"

        return ret

    def __str__(self):
        return self.get_full_description()

    def __unicode__(self):
        return self.get_full_description()

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.url != other.url:
            return False
        if self.mmd and other.mmd:
            if self.mmd.version != other.mmd.version:
                return False
            if self.mmd.release != other.mmd.release:
                return False
        return True
