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

default_config_path = "/etc/dnf/plugins/module.conf"

try:
    from configparser import ConfigParser
except:
    from ConfigParser import ConfigParser


class ModuleSection:
    def __init__(self, name, enabled, version, profiles):
        self._erase = False

        self._name = name
        self._enabled = enabled
        self._version = version
        self._installed_profiles = profiles

    @property
    def erase(self):
        return self._erase

    @erase.setter
    def erase(self, value):
        if not isinstance(value, bool):
            raise ValueError("ModuleSection.erase value has to be bool")
        self._erase = value


class ConfigFile(ConfigParser):
    def __init__(self, config_file=default_config_path):
        ConfigParser.__init__(self)
        self._config_file = config_file

    def load(self):
        self.read([self._config_file])

    def update_module(self, module_section):
        if module_section.erase:
            self.remove_section(module_section._name)
            return

        self.set(module_section._name, "enabled", module_section._enabled)
        self.set(module_section._name, "version", module_section._version)
        self.set(module_section._name, "profiles", module_section._installed_profiles)

        with open(self._config_file, 'w') as configfile:
            self.write(configfile)
