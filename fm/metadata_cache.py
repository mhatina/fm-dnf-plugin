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
import time

import modulemd
import fm.exceptions
from fm.module import Module
import errno

class CachedModuleMetadata(object):
    """
    Handles the module's metadata stored in the fm.cache_dir directory.
    """
    DEPENDING_MODS  = "_fm_data_depending_modules"
    CACHED_TIME     = "_fm_data_cached_time"
    REPO_NAME       = "_fm_data_repo_name"
    REPO_URL        = "_fm_data_repo_url"
    ENABLED_BY_USER = "_fm_enabled_by_user"

    def __init__(self, mmd = None):
        if mmd:
            self.mmd = mmd
        else:
            self.mmd = modulemd.ModuleMetadata()

        if not self.mmd.xmd:
            self.mmd.xmd = {}

        if not self.DEPENDING_MODS in self.mmd.xmd:
            self.mmd.xmd[self.DEPENDING_MODS] = []

        if not self.CACHED_TIME in self.mmd.xmd:
            self.refresh_cached_time()

    def set_repo_name(self, repo_name):
        self.mmd.xmd[self.REPO_NAME] = repo_name

    def set_repo_url(self, repo_url):
        self.mmd.xmd[self.REPO_URL] = repo_url

    def set_enabled_by_user(self, enabled):
        self.mmd.xmd[self.ENABLED_BY_USER] = enabled

    def refresh_cached_time(self):
        self.mmd.xmd[self.CACHED_TIME] = int(time.time())

    def add_depending_mod(self, mod):
        if not mod in self.mmd.xmd[self.DEPENDING_MODS]:
            self.mmd.xmd[self.DEPENDING_MODS].append(mod)

    def remove_depending_mod(self, mod):
        try:
            self.mmd.xmd[self.DEPENDING_MODS].remove(mod)
        except:
            pass

    def get_depending_mods(self):
        return self.mmd.xmd[self.DEPENDING_MODS]

    def load(self, mmd_file):
        mmd = modulemd.ModuleMetadata()

        try:
            mmd.load(mmd_file)
        except IOError:
            return

        self.mmd.xmd[self.DEPENDING_MODS] = mmd.xmd[self.DEPENDING_MODS]
        self.mmd.xmd[self.CACHED_TIME] = mmd.xmd[self.CACHED_TIME]
        if self.REPO_NAME in mmd.xmd:
            self.mmd.xmd[self.REPO_NAME] = mmd.xmd[self.REPO_NAME]
        if self.REPO_URL in mmd.xmd:
            self.mmd.xmd[self.REPO_URL] = mmd.xmd[self.REPO_URL]
        if self.ENABLED_BY_USER in mmd.xmd:
            self.mmd.xmd[self.ENABLED_BY_USER] = bool(mmd.xmd[self.ENABLED_BY_USER])

    def dump(self, mmd_file):
        try:
            self.mmd.dump(mmd_file)
        except PermissionError as err:
            raise fm.exceptions.Error(
                'Cannot open cache file: {}.'.format(err))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

class MetadataCache(object):
    """
    Class used to cache Module Metadata objects.
    """

    def __init__(self, cache_dir, opts):
        """
        Creates new MetadataCache instance.

        :param string cache_dir: Directory to which store the cached data.
        :param OptionsParser opts: Command line options.
        """
        #: Directory to which store the cached data.
        self.cache_dir = cache_dir
        #: Command line options
        self.opts = opts

        mkdir_p(self.cache_dir)

    def _get_mmd_file(self, mod):
        """
        Returns full path to cached mmd file for this module.
        """

        mmd_file = os.path.join(self.cache_dir, mod.name + "-" + mod.mmd.version
                                + "-" + mod.mmd.release + ".yaml")
        return mmd_file

    def store(self, mod, enabled_by_user = False):
        """
        Stores the module to cache.

        :param Module mod: Module instance to store in the cache.
        :param Bool enabled_by_user: True when module has been enabled by user.
        """

        mmd_file = self._get_mmd_file(mod)

        cached_mmd = CachedModuleMetadata(mod.mmd)
        cached_mmd.load(mmd_file)
        cached_mmd.refresh_cached_time()
        if not mod.api == self:
            cached_mmd.set_repo_name(mod.api.repo_name)
        cached_mmd.set_repo_url(mod.url)
        cached_mmd.set_enabled_by_user(enabled_by_user)
        cached_mmd.dump(mmd_file)

    def add_depending_mod(self, mod, name):
        """
        Adds depending module to the cache.

        :param Module mod: Module to which the dependency is added.
        :param string name: Name of the depending module.
        """
        mmd_file = self._get_mmd_file(mod)

        cached_mmd = CachedModuleMetadata(mod.mmd)
        cached_mmd.load(mmd_file)
        cached_mmd.add_depending_mod(name)
        cached_mmd.dump(mmd_file)

    def remove_depending_mod(self, mod, name):
        """
        Removes depending module from the cache.

        :param Module mod: Module from which the dependency is removed.
        :param string name: Name of the depending module.
        """
        mmd_file = self._get_mmd_file(mod)

        # Do not try to create the cache file if it does not exist.
        if not os.path.exists(mmd_file):
            return

        #print("Removing", name, "from list of depending mods on", mod.name)
        cached_mmd = CachedModuleMetadata(mod.mmd)
        cached_mmd.load(mmd_file)
        cached_mmd.remove_depending_mod(name)
        cached_mmd.dump(mmd_file)

    def get_depending_mods(self, mod):
        """
        Returns the string list of depending module names.

        :param Module mod: Module for which the depending mods list is returned.
        """
        mmd_file = self._get_mmd_file(mod)

        cached_mmd = CachedModuleMetadata(mod.mmd)
        cached_mmd.load(mmd_file)
        return cached_mmd.get_depending_mods()

    def load(self, mods, api_clients, enabled_by_user = None):
        """
        Loads the modules metadata from cache and adds them to Modules instance.

        :param Modules mods: Modules instance to which store the modules
        """
        for mmd_file in sorted(os.listdir(self.cache_dir)):
            mmd_file = os.path.join(self.cache_dir, mmd_file)
            mmd = modulemd.ModuleMetadata()
            mmd.load(mmd_file)

            api_client = None
            if mmd.xmd and CachedModuleMetadata.REPO_NAME in mmd.xmd:
                api_client = api_clients.get_api_client(mmd.xmd[CachedModuleMetadata.REPO_NAME])


            if api_client:
                repo_url = api_client.url + "/" + mmd.name
                if mmd.xmd and CachedModuleMetadata.REPO_URL in mmd.xmd:
                    repo_url = mmd.xmd[CachedModuleMetadata.REPO_URL]
            else:
                repo_url = None

            # Do not add module to `mods` when it is not enabled_by_user.
            if (enabled_by_user and (CachedModuleMetadata.ENABLED_BY_USER not in mmd.xmd
                    or enabled_by_user != mmd.xmd[CachedModuleMetadata.ENABLED_BY_USER])):
                continue

            mods.add_module(Module(api_client, mmd.name, repo_url, mmd, self.opts.root))

    def remove(self, mod):
        """
        Removes the module from the cache.

        :param Module mod: Module to remove from cache.
        """
        mmd_file = self._get_mmd_file(mod)
        os.remove(mmd_file)

    def is_cached(self, mod):
        """
        Returns True if the Module is in cache.

        :param Module mod: Module to look for in a cache.
        """
        mmd_file = self._get_mmd_file(mod)
        return os.path.exists(mmd_file)

    def is_valid(self, mod):
        """
        Returns True if the Module is in cache and is valid (not expired).

        :param Module mod: Module to look for in a cache.
        """
        if not mod.mmd or not mod.mmd.xmd:
            return False

        if not CachedModuleMetadata.CACHED_TIME in mod.mmd.xmd:
            return False

        metadata_expire = mod.get_metadata_expire()
        if metadata_expire > 0 and time.time() > mod.mmd.xmd[CachedModuleMetadata.CACHED_TIME] + metadata_expire:
            return False

        return True
