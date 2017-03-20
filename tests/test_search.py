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

class SearchTest(TestCase):

    
    def test_search_apr(self):
        ret = self.cli.run(self.params(["search", "--name", "apr"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "APR libraries module")

    def test_search_unknown(self):
        ret = self.cli.run(self.params(["search", "--name", "unknown"]))
        self.assertEqual(ret, 0)
        self.assertEqual(self.output.getvalue(), "")

    def test_search_version(self):
        ret = self.cli.run(self.params(["search", "--version", "==" , "2.4.18"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Apache")
        self.assertFind(self.output.getvalue(), "2.4.18")
    
    def test_search_multiple_httpd_modules(self):
        ret = self.cli.run(self.params(["search", "--name", "*ttpd"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Apache")
        self.assertFind(self.output.getvalue(), "httpd")
        self.assertFind(self.output.getvalue(), "2.2.15")
        self.assertFind(self.output.getvalue(), "2.4.18")

    def test_search_license_and_name(self):
        ret = self.cli.run(self.params(["search", "--name", "apr", "--license", "MIT"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "APR")
        self.assertFind(self.output.getvalue(), "0.1-1")

    def test_search_json_name_version(self):
        ret = self.cli.run(self.params(["search", "--json", '{"name":["httpd"], "version":["==", "2.4.18"]}']))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Apache")
        self.assertFind(self.output.getvalue(), "2.4.18-1")

    def test_requires_core(self):
        ret = self.cli.run(self.params(["search", "--requires", "core", "1.0"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "APR")
    
