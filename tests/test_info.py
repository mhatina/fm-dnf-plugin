# Copyright (C) 2012-2016  Red Hat, Inc.
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

from tests.support import TestCase, start_server, stop_server
from fm.cli import Cli
import fm.exceptions
import os

class InfoTest(TestCase):

    def test_info(self):
        ret = self.cli.run(self.params(["info", "apr"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Summary: APR libraries module")

    def test_info_version(self):
        ret = self.cli.run(self.params(["info", "httpd-2.2.15"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Version: 2.2.15")
        self.assertFind(self.output.getvalue(), "Release: 1")
        self.assertFind(self.output.getvalue(), "Release: 2")

    def test_info_version_release(self):
        ret = self.cli.run(self.params(["info", "httpd-2.2.15-1"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Version: 2.2.15")
        self.assertFind(self.output.getvalue(), "Release: 1")
        self.assertNotFind(self.output.getvalue(), "Release: 2")

    def test_info_profiles(self):
        ret = self.cli.run(self.params(["info", "core"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Profiles:\n")

    def test_info_bad_module(self):
        try :
            ret = self.cli.run(self.params(["info", "unknown"]))
        except fm.exceptions.Error as err:
            error = str(err)

        self.assertFind(error, "Unknown module")
