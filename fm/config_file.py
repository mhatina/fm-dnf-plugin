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
    def __init__(self, name, enabled=None, version=None, profiles=None):
        self._erase = False

        self._name = name
        self._enabled = enabled
        self._version = version
        self._profiles = profiles

    @property
    def erase(self):
        return self._erase

    @erase.setter
    def erase(self, value):
        if not isinstance(value, bool):
            raise ValueError("ModuleSection.erase value has to be bool")
        self._erase = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("ModuleSection.name value has to be string")
        self._name = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        if not isinstance(value, str):
            raise ValueError("ModuleSection.version value has to be string")
        self._version = value

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if not isinstance(value, str):
            raise ValueError("ModuleSection.enabled value has to be string")

        possible_values = ["yes", "no", "1", "0", "true", "false"]
        if value.lower() not in possible_values:
            raise ValueError("ModuleSection.enabled value has to be one of {}"
                             .format(possible_values))
        self._name = value

    @property
    def profiles(self):
        return self._profiles

    @profiles.setter
    def profiles(self, value):
        if not isinstance(value, list):
            raise ValueError("ModuleSection.profiles value has to be list")

        self._profiles = value


class ConfigFile(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self)
        self._config_file = default_config_path

    def load(self, config_file=None):
        self.read(config_file if config_file is not None else self._config_file)

    def get_installed_profiles(self):
        description = ""

        space_between_columns = 4
        max_name_width = max(len(section) for section in self.sections()) + space_between_columns

        description += "module".ljust(max_name_width)
        description += "profiles\n"

        for section in self.sections():
            description += section.ljust(max_name_width)
            description += "{}\n".format(self.get(section, "profiles"))

        return description[:-1]

    def update_module(self, module_section, removed=False):
        if module_section.erase:
            self.remove_section(module_section.name)
            return

        self.create_section_if_does_not_exist(module_section)
        installed_profiles = self.get_updated_profiles_list(module_section, removed)

        self.set(module_section.name, "enabled", module_section.enabled)
        self.set(module_section.name, "version", module_section.version)
        self.set(module_section.name, "profiles", ','.join(installed_profiles))

        with open(self._config_file, 'w') as configfile:
            self.write(configfile)

    def create_section_if_does_not_exist(self, module_section):
        if not self.has_section(module_section.name):
            self.add_section(module_section.name)

    def get_updated_profiles_list(self, module_section, removed):
        installed_profiles = None
        if self.has_option(module_section.name, "profiles"):
            installed_profiles = self.get(module_section.name, "profiles").split(",")
            if removed:
                for profile in module_section.profiles:
                    installed_profiles.remove(profile)
            else:
                module_section.profiles.extends(self.get(module_section.name, "profiles"))
        elif not removed:
            installed_profiles = module_section.profiles
        return installed_profiles
