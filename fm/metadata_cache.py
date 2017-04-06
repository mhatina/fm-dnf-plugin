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

import errno
import os
import time

import fm.exceptions
from fm.metadata import ModuleMetadataLoader
from fm.module import Module


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
            self.mmd = ModuleMetadataLoader()

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
        mmd = ModuleMetadataLoader()

        try:
            mmd.parse_yaml(mmd_file)
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

