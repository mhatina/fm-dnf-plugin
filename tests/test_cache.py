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
import time
from fm.metadata_cache import CachedModuleMetadata
import modulemd

class CacheTest(TestCase):

    def test_expiry_one_second(self):
        # Set metadata_expire to 1 second
        cfg = "[default]\nurl={}\nmetadata_expire=1".format("file://" + os.getcwd() + "/test-repo")
        f = open("./test.modules.d/default.cfg", "w")
        f.write(cfg)
        f.close()

        # Fill-in the Metadata cache with "list" request results
        ret = self.cli.run(self.params(["list"]))

        # Change the metadata file (set version to 4.0) and decrease the
        # CACHED_TIME to simulate the cache invalidation.
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd = CachedModuleMetadata(mmd)
        cached_mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd.mmd.xmd[CachedModuleMetadata.CACHED_TIME] -= 2
        cached_mmd.mmd.version = "4.0"
        cached_mmd.dump("./test.cache.d/available/core-1.0-1.yaml")

        # Cache is now invalid, so list should refetch the modules
        # again ...
        ret = self.cli.run(self.params(["list"]))
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")

        # ... and we should not see the version 4.0 anymore.
        self.assertEqual(mmd.version, "1.0")

    def test_expiry_never(self):
        # Set metadata_expire to 1 second
        cfg = "[default]\nurl={}\nmetadata_expire=never".format("file://" + os.getcwd() + "/test-repo")
        f = open("./test.modules.d/default.cfg", "w")
        f.write(cfg)
        f.close()

        # Fill-in the Metadata cache with "list" request results
        ret = self.cli.run(self.params(["list"]))

        # Change the metadata file (set version to 4.0) and decrease the
        # CACHED_TIME to simulate possible cache invalidation.
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd = CachedModuleMetadata(mmd)
        cached_mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd.mmd.xmd[CachedModuleMetadata.CACHED_TIME] -= 3600 * 24 * 365
        cached_mmd.mmd.version = "4.0"
        cached_mmd.dump("./test.cache.d/available/core-1.0-1.yaml")

        # Cache should remain valid ...
        ret = self.cli.run(self.params(["list"]))
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")

        # ... and we should not see the version 4.0 there.
        self.assertEqual(mmd.version, "4.0")

    def test_expiry_units(self):
        # Set metadata_expire to 1 second
        cfg = "[default]\nurl={}\nmetadata_expire=1h".format("file://" + os.getcwd() + "/test-repo")
        f = open("./test.modules.d/default.cfg", "w")
        f.write(cfg)
        f.close()

        # Fill-in the Metadata cache with "list" request results
        ret = self.cli.run(self.params(["list"]))

        # Change the metadata file (set version to 4.0) and decrease the
        # CACHED_TIME to simulate possible cache invalidation.
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd = CachedModuleMetadata(mmd)
        cached_mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd.mmd.xmd[CachedModuleMetadata.CACHED_TIME] -= 30 * 60
        cached_mmd.mmd.version = "4.0"
        cached_mmd.dump("./test.cache.d/available/core-1.0-1.yaml")

        # Cache should remain valid ...
        ret = self.cli.run(self.params(["list"]))
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")

        # ... and we should not see the version 4.0 there.
        self.assertEqual(mmd.version, "4.0")

        # Change the metadata file (set version to 4.0) and decrease the
        # CACHED_TIME to simulate possible cache invalidation.
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd = CachedModuleMetadata(mmd)
        cached_mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd.mmd.xmd[CachedModuleMetadata.CACHED_TIME] -= 31 * 60
        cached_mmd.mmd.version = "4.0"
        cached_mmd.dump("./test.cache.d/available/core-1.0-1.yaml")

        # Cache should be invalid now ...
        ret = self.cli.run(self.params(["list"]))
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")

        # ... and we should not see the version 1.0 there.
        self.assertEqual(mmd.version, "1.0")


    def test_cache_info(self):
        # Set metadata_expire to 1 second
        cfg = "[default]\nurl={}\nmetadata_expire=never".format("file://" + os.getcwd() + "/test-repo")
        f = open("./test.modules.d/default.cfg", "w")
        f.write(cfg)
        f.close()

        # Fill-in the Metadata cache with "list" request results
        ret = self.cli.run(self.params(["list"]))

        ret = self.cli.run(self.params(["info", "apr"]))
        self.assertEqual(ret, 0)
        self.assertFind(self.output.getvalue(), "Summary: APR libraries module")

    def test_cache_remove_unavailable(self):
        # Fill-in the Metadata cache with "list" request results
        ret = self.cli.run(self.params(["list"]))

        # Change the module name and dump it to different file to simulate
        # situation when we have module which has been already removed 
        # from the repository in the cache.
        mmd = modulemd.ModuleMetadata()
        mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd = CachedModuleMetadata(mmd)
        cached_mmd.load("./test.cache.d/available/core-1.0-1.yaml")
        cached_mmd.mmd.name = "foobar"
        cached_mmd.dump("./test.cache.d/available/foobar-1.0-1.yaml")

        # Refresh the cache - module should get removed from the available
        # cache.
        ret = self.cli.run(self.params(["refresh"]))

        # .. reset the output
        self.output.truncate(0)
        self.output.seek(0)

        # List the modules to check the module is not in the output
        ret = self.cli.run(self.params(["list"]))
        self.assertNotFind(self.output.getvalue(), "foobar")
