# Copyright (C) 2012-2016  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Written by Jan Kaluza

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser

import io

import fm.exceptions

class ConfigFile(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self)

    def set_defaults(self):
        if not self.has_section("fm"):
            self.add_section("fm")

        if not self.has_option("fm", "modules_dir"):
            self.set("fm", "modules_dir", "/etc/fm.modules.d")

        if not self.has_option("fm", "cache_dir"):
            self.set("fm", "cache_dir", "/var/cache/fm")

    def load(self, config_file):
        self.read([config_file])
        self.set_defaults()

    def loads(self, config):
        self.readfp(io.StringIO(config))
        self.set_defaults()

    def get_modules_dir(self):
        return self.get("fm", "modules_dir")

    def get_cache_dir(self):
        return self.get("fm", "cache_dir")
