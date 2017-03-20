# repo_file.py
# DNF Repo file implementation.
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

class RepoFile(object):
    """
    Class representing DNF Repo file.
    """

    def __init__(self, name, url, root = "/"):
        """
        Creates new Fedora Module representation.

        :param APIClient api: APIClient implementation.
        :param string name: Name of the module.
        :param modulemd.ModuleMetadata: Module metadata if available.
        """
        self.name = name
        self.url = url
        self.root = root

    def get_filename(self):
        """
        Returns full path to the repository file describing this module.

        :param string root: Full path to root file-system.
        :return: Full path to repository file.
        :rtype: string
        """
        return os.path.join(self.root, "etc/yum.repos.d/_fm_{}.repo").format(self.name)

    def get_repo_name(self):
        return "_fm_{}".format(self.name)

    def create(self):
        """
        Creates the repository file on file-system.

        :raises fm.exceptions.Error: If the repo file cannot be created.
        """
        repo_filename = self.get_filename()

        try:
            f = open(repo_filename, "w")
        except IOError as err:
            raise fm.exceptions.Error(
                'Cannot create repo file: {}'.format(err))

        data =  "[{}]\n".format(self.get_repo_name())
        data += "name=Modularization repository for {}\n".format(self.name)
        data += "baseurl={}\n".format(self.url)
        data += "gpgcheck=0\n"
        data += "priority=50\n" # DNF default in 99
        data += "enabled=1\n"

        f.write(data)
        f.close()
        os.chmod(repo_filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

    def remove(self):
        """
        Removes the repository file from file-system

        :raises fm.exceptions.Error: If the repo file cannot be removed.
        """
        repo_filename = self.get_filename()
        try:
            os.remove(repo_filename)
        except OSError as err:
            raise fm.exceptions.Error(
                'Cannot remove repo file: {}'.format(err))

    def is_created(self):
        """
        Returns True if the repo file is created.

        :return: True if the repo file is created.
        :rtype: bool
        """
        return os.path.exists(self.get_filename())

