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


class OptionParser(argparse.ArgumentParser):
    """
    Subclass to handle command line switches.
    """

    def __init__(self, **kwargs):
        argparse.ArgumentParser.__init__(self, add_help=False, **kwargs)
        self._addBasicOptions()

    def _addBasicOptions(self):
        self.add_argument("-v", "--verbose", action="store_true",
                           default=None, help="Show verbose output.")
        self.add_argument("-c", "--config", action="store",
                           default="/etc/dnf/plugins/module.conf",
                           help="Configuration file.")
        self.add_argument("-r", "--root", action="store",
                           default="/",
                           help="Path to root directory of the filesystem.")
        self.add_argument("-n", "--no-dnf", action="store_true",
                           default=False,
                           help="Do not call DNF during enable/disable.")
        self.add_argument("-y", "--assumeyes", action="store_true",
                           default=False,
                           help="Automatically answer yes for all questions")
        self.add_argument("--show-requirements", action="store_true",
                           default=False,
                           help="Show requirements of modules which are hidden by default.")

    def get_usage(self):
        """
        Returns the usage information to show to the user.

        :return: Usage string.
        :rtype: string
        """
        usage = ""
        options = self.format_help().split('\n')
        for option in options[3:]:
            usage += "    " + option.strip() + "\n"
        return usage
