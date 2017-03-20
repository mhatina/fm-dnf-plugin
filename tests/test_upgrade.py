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
from fm.metadata_cache import CachedModuleMetadata
import dnf

class UpgradeTest(TestCase):

    def test(self):
        pass

    #def test_upgrade_httpd(self):
        ## Enable httpd-2.2.15-1
        #ret = self.cli.run(self.params(["enable", "httpd-2.2.15-1",  "-n"]))
        #self.assertEqual(ret, 0)
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-1.yaml"))

        ## .. reset the output
        #self.output.truncate(0)
        #self.output.seek(0)

        ## Try to upgrade to latest httpd-2.2.15-2
        #ret = self.cli.run(self.params(["upgrade", "httpd", "-n"]))
        #self.assertEqual(ret, 0)
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-2.yaml"))


    #def test_upgrade_httpd_dnf(self):
        ## Enable httpd-2.2.15-1
        #ret = self.cli.run(self.params(["enable", "httpd-2.2.15-1",  "-n"]))
        #self.assertEqual(ret, 0)
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        #self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-1.yaml"))

        ## .. reset the output
        #self.output.truncate(0)
        #self.output.seek(0)

        ## Try to upgrade to latest httpd-2.2.15-2
        #try:
            #ret = self.cli.run(self.params(["upgrade", "httpd"]))
        #except dnf.exceptions.Error as err:
            #error = str(err)
            #ret = 0

        #self.assertEqual(error, 'Cannot get list of packages: dnf repository-packages _fm_httpd list installed')
