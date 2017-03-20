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

class ProfilesTest(TestCase):

    def test(self):
        pass

    #def test_default_profile_enable(self):
        ## 1. Enable the "core" module. Test that it tries to install RPMs
        ## from default profile.
        #try:
            #ret = self.cli.run(self.params(["enable", "core"]))

        #except fm.exceptions.Error as err:
            #error = str(err)
            #ret = 0

        #self.assertEqual(error, 'Cannot execute dnf command: dnf repository-packages _fm_core install bar  --allowerasing')
        #self.assertEqual(ret, 0)
        #self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))

    #def test_another_profile_enable(self):
        #try:
            #ret = self.cli.run(self.params(["enable", "core", "minimal"]))

        #except fm.exceptions.Error as err:
            #error = str(err)
            #ret = 0

        #self.assertEqual(error, 'Cannot execute dnf command: dnf repository-packages _fm_core install foo  --allowerasing')
        #self.assertEqual(ret, 0)
        #self.assertTrue(not os.path.exists("./test_root/etc/yum.repos.d/_fm_core.repo"))
