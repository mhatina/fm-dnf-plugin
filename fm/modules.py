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
import os
import requests
from collections import OrderedDict

import modulemd
import fm.exceptions
from fm.module import Module
from fm.metadata_cache import MetadataCache
from fm.fm_modules_resolver import FmModulesResolver
from fm.modules_search import ModulesSearch
import fnmatch
import re


class Modules(OrderedDict):
    """
    OrderedDict subclass containing modules, allowing their enablement
    and disablement.
    """

    def __init__(self, cfg, opts, api_clients):
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
        #: APIClients instance.
        self.api_clients = api_clients

        self.disable_cache = False

        self.enabled_cache = MetadataCache(self.cfg.get_cache_dir() + "/enabled", self.opts)
        self.available_cache = MetadataCache(self.cfg.get_cache_dir() + "/available", self.opts)

    def set_metadata_expire(self, seconds):
        self.available_cache.set_metadata_expire(seconds)

    def load_enabled_modules(self, enabled_by_user = None):
        """
        Loads enabled modules' metadata.
        """

        self.disable_cache = True
        self.enabled_cache.load(self, self.api_clients, enabled_by_user)
        self.disable_cache = False

    def load_available_modules(self):
        """
        Loads available modules' metadata.
        """

        self.disable_cache = True
        self.available_cache.load(self, self.api_clients)
        self.disable_cache = False

    def merge(self, mods, keep_order = False):
        """
        Merges another Modules instance with this one.

        :param Modules mods: Modules instance to merge with this one.
        :param keep_order: True when result of the merge should be ordered.
        """
        # When the result of some command does not output list
        # of the modules, we do not care about ordering...
        # TODO
        #if not keep_order:
            #self.update(mods)
            #return

        keys = list(self.keys()) + list(mods.keys())
        for key in sorted(keys):
            if key in self:
                # We need to keep order of modules. So even when we store
                # the module already, it is not in the right order, so we remove
                # it and create it again in the end of the ordered dict.
                m = self[key]
                del self[key]
                self[key] = m
                if key in mods:
                    self[key] += sorted(mods[key], key = lambda mod: (mod.mmd.version, int(mod.mmd.release)))
            else:
                self[key] = sorted(mods[key], key = lambda mod: (mod.mmd.version, int(mod.mmd.release)))

    def enable(self, name, profiles):
        """
        Enables module and all the depending modules. Also updates
        cached metadata stored in fm.cache_dir.

        :param string name: Name of the module to enable.
        :param string version: Version of the module to enable.
        """

        resolver = FmModulesResolver(self)
        resolver.execute("enable", name, profiles)

    def disable(self, name):
        """
        Disables module and all the modules which depend on this module.
        Also updates the metadata stored in fm.cache_dir.

        :param string name: Name of the module to disable.
        """

        resolver = FmModulesResolver(self)
        resolver.execute("disable", name)

    def search(self, keywords):
        """
        Searches for modules and returns the Modules instance containing
        modules matching the keyword.

        :param dictionary keywords: Dictionary of keywords to search for.
        """

        mods_search = ModulesSearch(self)
        return mods_search.search(keywords)

    def check_upgrade(self, names = None):
        """
        Returns the list of modules for which the upgrade is available.
        """

        if not names or len(names) == 0:
            names = self.keys()

        to_upgrade = Modules(self.cfg, self.opts, self.api_clients)
        for name in names:
            enabled_mod = self.get_enabled_module(name)
            if not enabled_mod:
                continue

            available_mods = self.get_modules(name, enabled_mod.mmd.version)
            available_mods = sorted(available_mods, key = lambda mod: int(mod.mmd.release))
            latest_mod = available_mods[-1]
            if latest_mod != enabled_mod:
                to_upgrade.add_module(latest_mod, False)
        return to_upgrade

    def check_rebase(self, names = None):
        """
        Returns the list of modules for which the upgrade is available.
        """
        if not names or len(names) == 0:
            names = self.keys()

        to_upgrade = Modules(self.cfg, self.opts, self.api_clients)
        for name in names:
            enabled_mod = self.get_enabled_module(name)
            if not enabled_mod:
                continue
            available_mods = self.get_modules(name)
            available_mods = sorted(available_mods, key = lambda mod: (mod.mmd.version, int(mod.mmd.release)))
            latest_mod = available_mods[-1]
            if latest_mod != enabled_mod:
                to_upgrade.add_module(latest_mod, False)
        return to_upgrade

    def upgrade(self, names):
        """
        Upgrades the modules to latest release.
        """

        for name in names:
            enabled_mod = self.get_enabled_module(name)
            if not enabled_mod:
                raise fm.exceptions.DependencyError("Module {} is not enabled".format(name))

            available_mods = self.get_modules(name, enabled_mod.mmd.version)
            available_mods = sorted(available_mods, key = lambda mod: int(mod.mmd.release))
            latest_mod = available_mods[-1]

            resolver = FmModulesResolver(self)
            resolver.execute("enable", latest_mod.get_nvr())

    def _name_to_nvr(self, name):
        lst = name.split("-")
        if len(lst) < 2:
            return name, None, None

        if len(lst) > 2:
            try:
                int(lst[-2][0])
                release = str(int(lst[-1]))
                version = lst[-2]
                return '-'.join(lst[:-2]), version, release
            except:
                pass

        if len(lst) > 1:
            try:
                int(lst[-1][0])
                version = lst[-1]
                return '-'.join(lst[:-1]), version, None
            except:
                return name, None, None

        return name, None, None

    def rebase(self, nvr, profiles):
        """
        Rebases the module named `name` to version defined by `nvr.
        """

        name, version, release = self._name_to_nvr(nvr)
        enabled_mod = self.get_enabled_module(name)
        if not enabled_mod:
            raise fm.exceptions.DependencyError("Module {} is not enabled".format(name))

        available_mods = self.get_modules(name, version, release)
        available_mods = sorted(available_mods, key = lambda mod: (mod.mmd.version, int(mod.mmd.release)))
        latest_mod = available_mods[-1]

        resolver = FmModulesResolver(self)
        resolver.execute("enable", latest_mod.get_nvr(), profiles)

    def is_cache_valid(self, name = None):
        """
        Returns True if the cache is in valid state. When `name` is specified,
        this method checks only particular module and not all modules in cache.
        """
        # If we do not have any module, the cache is not valid, because
        # we want to fetch the modules list.
        if len(self) == 0:
            return False

        if name:
            if not name in self:
                return False
            for mod in self[name]:
                if not self.available_cache.is_valid(mod):
                    return False
            return True

        for mods in self.values():
            for mod in mods:
                if not self.available_cache.is_valid(mod):
                    return False
        return True

    def eewwrefresh_cache(self):
        """
        Stores all the current Module's metadata to available modules cache.
        """

        for mods in self.values():
            for mod in mods:
                self.available_cache.store(mod)

    def remove_old_cached_modules(self):
        """
        Removes modules which are in cache, but are not in this Modules
        instance from the cache.
        """

        # Load the cached modules.
        cached_mods = Modules(self.cfg, self.opts, self.api_clients)
        self.available_cache.load(cached_mods, self.api_clients)

        # Find out the modules which are in cache but are not in this
        # Modules instance and remove them from cache.
        for mods in cached_mods.values():
            for mod in mods:
                our_modules = self.get_modules(mod.name, mod.mmd.version,
                                               mod.mmd.release)
                if not our_modules or len(our_modules) == 0:
                    self.available_cache.remove(mod)

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

    def get_modules(self, name, version = None, release = None):
        """
        Returns all modules matching the `name` and `version` or `release`
        when defined.
        """

        if not name in self:
            return None

        mods = []
        for mod in self[name]:
            if version and mod.mmd.version != version:
                continue
            if release and mod.mmd.release != release:
                continue
            mods.append(mod)

        return mods

    def get_enabled_module(self, name):
        """
        Returns the Module instance with name `name` which is enabled
        on the system.
        """

        if not name in self:
            raise fm.exceptions.DependencyError("Unknown module {}".format(name))

        mods = self[name]
        enabled_mod = None
        for mod in mods:
            if mod.is_enabled() and self.enabled_cache.is_cached(mod):
                enabled_mod = mod
                break

        return enabled_mod

    def get_full_description(self, nvr):
        """
        Returns full description of all modules matching the specified `nvr`.
        """
        name, version, release = self._name_to_nvr(nvr)
        mods = self.get_modules(name, version, release)
        if not mods or len(mods) == 0:
            raise fm.exceptions.DependencyError("Unknown module {}".format(nvr))

        mods = sorted(mods, key = lambda mod: (mod.mmd.version, int(mod.mmd.release)))

        ret = ""
        did_fetch = False
        for mod in mods:
            if mod.fetch_module_metadata():
                did_fetch = True
            ret += mod.get_full_description() + "\n"
        if did_fetch:
            self.refresh_cache()
        return ret[:-1] # remove last '\n'

    def get_brief_description(self):
        """
        Returns brief description of all modules in this Modules instance.
        """

        if len(self) == 0:
            return ""

        # Get the maximum width of the text we will show in each column
        # of output.
        max_name_width = max(len(word) for word in self.keys()) + 4  # padding
        max_vr_width = (max(len(mod.mmd.version) + 1 + 
                            len(mod.mmd.release) for mods in self.values()
                            for mod in mods) + 4)  # padding

        ret = ""
        for mods in self.values():
            for mod in mods:
                vr = mod.mmd.version + "-" + mod.mmd.release

                # Show output in 3 columns...
                ret += mod.name.ljust(max_name_width)
                ret += vr.ljust(max_vr_width)
                ret += mod.mmd.summary
                ret += "\n"

        return ret[:-1] # remove last '\n'
