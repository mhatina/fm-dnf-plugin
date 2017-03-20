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

class EnableDisableTest(TestCase):

    def test_enable_core_disable_core(self):
        # 1. Enable the "core" module. The _fm_core.repo should be created.
        ret = self.cli.run(self.params(["enable", "core",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))

        f = open("./test_root/etc/yum.repos.d/_fm_core.repo")
        data = f.read()
        f.close()
        self.assertFind(data, "[_fm_core]")

        # 2. Check that list-enabled lists core module.
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "core")

        # Check that the yaml file with enable module exists
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))

        # Load the CachedModuleMetadata and checks its content
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/core-1.0-1.yaml")
        self.assertLength(cached_mmd.get_depending_mods(), 0)

        # .. reset the output
        self.output.truncate(0)
        self.output.seek(0)

        # 3. Disable the module. The _fm_core.repo should be removed.
        ret = self.cli.run(self.params(["disable", "core", "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))

        # 4. Check that list-enabled does not list core module.
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertEqual(self.output.getvalue(), "")

        # Check that the yaml file with enable module does not exist
        self.assertTrue(not os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))

    def test_enable_apr_disable_apr(self):
        # 1. Enable the "apr" module. Both core and apr repos should be enabled
        ret = self.cli.run(self.params(["enable", "apr",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_apr.repo"))

        # 1. Check that list-enabled lists apr module.
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertNotFind(self.output.getvalue(), "core")
        self.assertFind(self.output.getvalue(), "apr")

        # Check that the yaml file with enable module exists
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))

        # Load the CachedModuleMetadata and checks its content - apr
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/apr-0.1-1.yaml")
        self.assertLength(cached_mmd.get_depending_mods(), 0)

        # Load the CachedModuleMetadata and checks its content - core
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/core-1.0-1.yaml")
        self.assertEqual(cached_mmd.get_depending_mods()[0], "apr")

        # .. reset the output
        self.output.truncate(0)
        self.output.seek(0)

        # 3. Disable the core module. APR module should be removed
        ret = self.cli.run(self.params(["disable", "apr", "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
        self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_apr.repo"))

        # 4. Check that list-enabled lists core module
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertNotFind(self.output.getvalue(), "core")

        # Check that the yaml file with enable module does not exist
        self.assertTrue(not os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        self.assertTrue(not os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))

        # Load the CachedModuleMetadata and checks its content - core
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/core-1.0-1.yaml")
        self.assertLength(cached_mmd.get_depending_mods(), 0)

    def test_enable_apr_disable_core(self):
        # 1. Enable the "apr" module. Both core and apr repos should be enabled
        ret = self.cli.run(self.params(["enable", "apr",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_apr.repo"))

        # 1. Check that list-enabled lists apr module.
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertNotFind(self.output.getvalue(), "core")
        self.assertFind(self.output.getvalue(), "apr")

        # Check that the yaml file with enable module exists
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))

        # Load the CachedModuleMetadata and checks its content - core
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/apr-0.1-1.yaml")
        self.assertLength(cached_mmd.get_depending_mods(), 0)

        # Load the CachedModuleMetadata and checks its content - apr
        cached_mmd = CachedModuleMetadata()
        cached_mmd.load("./test.cache.d/enabled/core-1.0-1.yaml")
        self.assertEqual(cached_mmd.get_depending_mods()[0], "apr")

        # .. reset the output
        self.output.truncate(0)
        self.output.seek(0)

        # 3. Disable the core module. Both modules should be removed
        ret = self.cli.run(self.params(["disable", "core", "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
        self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_apr.repo"))

        # 4. Check that list-enabled does not list any module.
        ret = self.cli.run(self.params(["list-enabled"]))
        self.assertEqual(ret, 0)
        self.assertEqual(self.output.getvalue(), "")

        # Check that the yaml file with enable module does not exist
        self.assertTrue(not os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))

    def test_disable_unknown(self):
        try:
            ret = self.cli.run(self.params(["disable", "unknown", "-n"]))
        except fm.exceptions.Error as err:
            error = str(err)

        self.assertEqual(error, "No such module: unknown")

    def test_enable_httpd_latest(self):
        # Check that it installs the latest available httpd when no specific
        # version is set
        ret = self.cli.run(self.params(["enable", "httpd",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.4.18-1.yaml"))

    def test_enable_httpd_specific_version_latest_release(self):
        # Check that it installs the latest available httpd when no specific
        # version is set
        ret = self.cli.run(self.params(["enable", "httpd-2.2.15",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-2.yaml"))

    def test_enable_httpd_specific_version_release(self):
        # Check that it installs the latest available httpd when no specific
        # version is set
        ret = self.cli.run(self.params(["enable", "httpd-2.2.15-1",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-1.yaml"))

    def test_enable_httpd_specific_version_release2(self):
        # Check that it installs the latest available httpd when no specific
        # version is set
        ret = self.cli.run(self.params(["enable", "httpd-2.2.15-2",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test.cache.d/enabled/core-1.0-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/apr-0.1-1.yaml"))
        self.assertTrue(os.path.exists("./test.cache.d/enabled/httpd-2.2.15-2.yaml"))

    def test_enable_apr_disable_core_show_requirements(self):
        # 1. Enable the "apr" module. Both core and apr repos should be enabled
        ret = self.cli.run(self.params(["enable", "apr",  "-n"]))
        self.assertEqual(ret, 0)
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
        self.assertTrue(os.path.exists("./test_root/etc/yum.repos.d/_fm_apr.repo"))

        # 1. Check that list-enabled lists apr module.
        ret = self.cli.run(self.params(["list-enabled", "--show-requirements"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "core")
        self.assertFind(self.output.getvalue(), "apr")
