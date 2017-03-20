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

class RepoConfigFile(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self)

    def load(self, config_file):
        self.read([config_file])

    def loads(self, config):
        self.readfp(io.StringIO(config))
        self.set_defaults()

    def is_enabled(self, repo_name):
        try:
            if (self.has_option(repo_name, "enabled")
                and not self.getboolean(repo_name, "enabled")):
                return False
        except ValueError as err:
            raise fm.exceptions.ConfigFileError(
                'Value of "enabled" option is not boolean: {}.'.format(err))
        return True

    def get_metadata_expire(self, repo_name):
        MULTS = {'d': 60 * 60 * 24, 'h' : 60 * 60, 'm' : 60, 's': 1}

        if self.has_option(repo_name, "metadata_expire"):
            s = self.get(repo_name, "metadata_expire")
        else:
            s = "6h"

        if len(s) < 1:
            raise ValueError("no value specified")

        if s == "-1" or s == "never": # Special cache timeout, meaning never
            return -1

        if s[-1].isalpha():
            n = s[:-1]
            unit = s[-1].lower()
            mult = MULTS.get(unit, None)
            if not mult:
                raise ValueError("unknown unit '%s'" % unit)
        else:
            n = s
            mult = 1

        try:
            n = float(n)
        except (ValueError, TypeError):
            raise ValueError('invalid value')

        if n < 0:
            raise ValueError("seconds value may not be negative")

        return n * mult
