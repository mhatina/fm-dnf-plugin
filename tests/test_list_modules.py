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

from __future__ import unicode_literals
from tests.support import TestCase, start_server, stop_server
from fm.cli import Cli
import fm.exceptions
import os

#class ListModulesTest(TestCase):

    #def test_list_modules_no_module(self):
        #self.setupServer('[{"status": "Approved", "upstream_url": "", "koschei_monitor": true, "monitor": false, "description": "This is a test module for the modularity working group stuff.", "namespace": "modules", "summary": "A test module for modularity in stg", "acls": [], "modulemd": "document: modulemd\\nversion: 0\\ndata:\\n        name: testmodule\\n        version: 1.0\\n        release: 1\\n        summary: A test module\\n        description: >\\n                A module for the demonstration of the metadata format. Also,\\n                the obligatory lorem ipsum dolor sit amet goes right here.\\n        license:\\n                module:\\n                        - MIT\\n                content: []\\n        xmd: ~\\n        dependencies:\\n                buildrequires:\\n                        core: 23\\n                        c-build: 6.0\\n                requires:\\n                        core: 23\\n        references:\\n                community: http://www.example.com/\\n                documentation: http://www.example.com/\\n                tracker: http://www.example.com/\\n        components:\\n                rpms:\\n                        dependencies: True\\n                        fulltree: True\\n                        packages:\\n                                bar:\\n                                        repository: https://pagure.io/bar.git\\n                                        cache: https://example.com/cache\\n                                        commit: 26ca0c0\\n                                baz: ~\\n                                xxx:\\n                                        arches: [ i686, x86_64 ]\\n                                        multilib: [ x86_64 ]\\n                                xyz: ~\\n", "_id": {"$oid": "5735a33384a25f6298fb5e0a"}, "review_url": "https://bugzilla.redhat.com/12345", "creation_date": 1460472886.0, "name": "testmodule"}]')

        #ret = self.cli.run(self.params(["list-enabled"]))
        #self.assertEqual(ret, 0)
        #self.assertEmpty(self.output.getvalue())

    #def test_list_modules_one_module(self):
        #self.setupServer('[{"status": "Approved", "upstream_url": "", "koschei_monitor": true, "monitor": false, "description": "This is a test module for the modularity working group stuff.", "namespace": "modules", "summary": "A test module for modularity in stg", "acls": [], "modulemd": "document: modulemd\\nversion: 0\\ndata:\\n        name: testmodule\\n        version: 1.0\\n        release: 1\\n        summary: A test module\\n        description: >\\n                A module for the demonstration of the metadata format. Also,\\n                the obligatory lorem ipsum dolor sit amet goes right here.\\n        license:\\n                module:\\n                        - MIT\\n                content: []\\n        xmd: ~\\n        dependencies:\\n                buildrequires:\\n                        core: 23\\n                        c-build: 6.0\\n                requires:\\n                        core: 23\\n        references:\\n                community: http://www.example.com/\\n                documentation: http://www.example.com/\\n                tracker: http://www.example.com/\\n        components:\\n                rpms:\\n                        dependencies: True\\n                        fulltree: True\\n                        packages:\\n                                bar:\\n                                        repository: https://pagure.io/bar.git\\n                                        cache: https://example.com/cache\\n                                        commit: 26ca0c0\\n                                baz: ~\\n                                xxx:\\n                                        arches: [ i686, x86_64 ]\\n                                        multilib: [ x86_64 ]\\n                                xyz: ~\\n", "_id": {"$oid": "5735a33384a25f6298fb5e0a"}, "review_url": "https://bugzilla.redhat.com/12345", "creation_date": 1460472886.0, "name": "testmodule"}]')

        #f = open("./test_root/etc/yum.repos.d/_fm_yakuake.repo", "w")
        #f.write("[_fm_yakuake]")
        #f.close()

        #ret = self.cli.run(self.params(["list-enabled"]))
        #self.assertEqual(ret, 0)
        #self.assertFind(self.output.getvalue(), "Name: yakuake")
