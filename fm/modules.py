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


"""
Client for fm-metadata-server API.
"""

from __future__ import print_function

from collections import OrderedDict

import fm.exceptions
from fm.metadata import ModuleMetadataLoader
from fm.modules_resolver.modules_resolver import FmModulesResolver
from fm.modules_search import ModulesSearch


class Modules(OrderedDict):
    """
    OrderedDict subclass containing modules, allowing their enablement
    and disablement.
    """

    def __init__(self, cfg, opts):
        """
        Creates new Modules instance.

        :param ConfigFile cfg: Configuration file.
        :param OptionsParser opts: Command line options.
        """
        OrderedDict.__init__(self)
        #: Configuration file.
        self.cfg = cfg
        #: Command line options.
        self.opts = opts

        self.disable_cache = False
        self.dnfbase = fm.dnfbase.base

        self.available_repos = []
        for module in self.dnfbase.repos.iter_module():
            self.available_repos.append(module)

        self.enabled_modules = []

    def load_modules(self):
        for repo in self.available_repos:
            for metadata in ModuleMetadataLoader(repo).load():
                self[metadata.name] = metadata

    def search(self, keywords):
        """
        Searches for modules and returns the Modules instance containing
        modules matching the keyword.

        :param dictionary keywords: Dictionary of keywords to search for.
        """

        mods_search = ModulesSearch(self)
        return mods_search.search(keywords)

    def add_module(self, mod, cache = True):
        """
        Adds new module to this Modules instance.
        """

        if not mod.name in self:
            self[mod.name] = []

        self[mod.name].append(mod)

        # Cache the module.
        if cache and mod.mmd and not self.available_cache.is_valid(mod) and not self.disable_cache:
            self.available_cache.store(mod)

    def get_modules(self, name, version=None):
        """
        Returns all modules matching the `name` and `version`
        when defined.
        """

        if name not in self:
            return None

        mods = []
        for mod in self.values():
            if (version and mod.version != version) or name != mod.name:
                continue
            mods.append(mod)

        return mods

    def get_full_description(self, name):
        mods = self.get_modules(name)
        if not mods or len(mods) == 0:
            raise fm.exceptions.DependencyError("Unknown module {}".format(name))

        mods = sorted(mods, key=lambda module: module.version)

        ret = ""
        for mod in mods:
            ret += mod.dump_to_string() + "\n"
        return ret[:-1] # remove last '\n'

    def get_brief_description(self, only_enabled=False):
        """
        Returns brief description of all modules in this Modules instance.
        """

        if len(self) == 0:
            return ""

        # Get the maximum width of the text we will show in each column
        # of output.
        max_name_width = max(len(name) for name in self.keys()) + 4  # padding
        max_vr_width = (max(len(str(mod.version)) for mod in self.values()) + 4)  # padding

        ret = ""
        for module_metadata in self.values():
            if only_enabled and module_metadata.is_enabled():
                continue

            vr = str(module_metadata.version)

            # Show output in 3 columns...
            ret += module_metadata.name.ljust(max_name_width)
            ret += vr.ljust(max_vr_width)
            ret += module_metadata.summary
            ret += "\n"

        return ret[:-1]  # remove last '\n'
