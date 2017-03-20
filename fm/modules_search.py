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
# Written by Jan Kaluza, Courtney Pacheco


from __future__ import print_function
import os
import requests
from collections import OrderedDict

import modulemd
import fm.exceptions
from fm.module import Module
from fm.metadata_cache import MetadataCache
from fm.fm_modules_resolver import FmModulesResolver
import fnmatch
import re
import fm.modules


class ModulesSearch(object):
    """
    Searches for modules from Modules instance.
    """

    def __init__(self, mods):
        """
        Creates new ModulesSearch instance.

        :param Modules mods: Modules to search in.
        """
        #: Modules
        self.mods = mods

    def search(self, keywords):
        """
        Searches for modules and returns the Modules instance containing
        modules matching the keyword.

        :param dictionary keywords: Dictionary of keywords to search for.
        """

        matching = fm.modules.Modules(self.mods.cfg, self.mods.opts,
                                      self.mods.api_clients)

        if len(keywords) == 0:
            return matching
 
        # STEP 1: Gather a list of modules
        # If '_name' in dict, let's keep it simple so that the next step
        # is faster...
        modules = self._gather_modules(keywords)

        # STEP 2: Let's search through 'modules' to find the module that meets
        #         our full search criteria.
        results = []
 
        version_exists = False
        release_exists = False
        
        if "_version" in keywords:
            version_exists = True

        if "_release" in keywords:
            release_exists = True

        # Start with iterating through the entire module list and get all
        # the module metadata keys (e.g., _name, _release, etc.)
        for module in modules:
            metadata_names = vars(module.mmd)
            matches = True

            # For each module in the list of modules, we find where the metadata
            # completely meets our full criteria. The 'matches' boolean variable
            # tells us if any of the criteria is not met.
            for key in metadata_names.keys():
                if key not in keywords:
                    continue
            
                    if version_exists == True and key == "_version":
                        continue
                    elif release_exists == True and key == "_release":
                        continue
                    else:
                        if key == "_requires":
                            if metadata_names[key] != keywords[key]:
                                matches = False
                                break
                        elif metadata_names[key] not in keywords[key]:
                            matches = False
                            break
  
            # If the criteria is 100% met for the given module, add it to the
            # resulting list of modules
            if matches and module not in results:
                results.append(module)
        

        # STEP 4: Add the resulting modules to 'matching' and pass 'matching'
        #         back to cli.py so that we can get a brief description
        #         of each module and print it out to the command line.
        for item in results:
            matching.add_module(item, False)
        return matching

    def _gather_modules(self, keywords):
        '''
        Returns a list of modules for a given keywords dictionary

        :param keywords: Dictionary of keywords to search for
        '''
        modules = []

        #Parse 'version' and/or 'release'  first because they're most difficult to deal with
        if "_version" in keywords:
            modules = self._parse_version_or_release(keywords, "_version")
            wildcards = self._check_for_wildcards_in_name(keywords)

            if "_release" in keywords:
                tmp = []
                release = keywords["_release"][1]
                inequality = keywords["_release"][0]
                for mod in modules:
                    mmd = mod.mmd.release
                    tmp = self._get_modules_by_inequality("_release", inequality, release, tmp, mod)
                modules = tmp
            
            if wildcards == True:
                self._parse_name(keywords, modules)
                

        elif "_release" in keywords:
            modules = self._parse_version_or_release(keywords, "_release")
            wildcards = self._check_for_wildcards_in_name(keywords)
            if wildcards == True:
                self._parse_name(keywords, modules)

        elif "_name" in keywords:
            modules = self._parse_name(keywords, [])

        else:
            for name, mods in self.mods.items():
                for mod in mods:
                    modules.append(mod)

        return modules


    def _parse_name(self, keywords, modules=[]):
        """
        Parse the name for each module in the entire database
        
        :param keywords: dictionary of keywords to search for
        """
        if not modules:
            module_names = keywords["_name"] 

            for mod_name in module_names:

                for name, mods in self.mods.items():
                    if mod_name == name:
                        modules.extend(mods)

                    #Handle wildcards using regex to find matching names. For any name match,
                    #append the matching name to the end of 'module_names' so that it gets
                    #parsed
                    elif "*" in mod_name:
                        name_regex = fnmatch.translate(mod_name)
                        reobj = re.compile(name_regex)
                        matches = [m.group(0) for mod in mods for m in [reobj.search(mod.name)] if m]
                        for match in matches:
                            if (match not in module_names):
                                module_names.append(match)

        else:
            module_names = keywords["_name"]
            tmp = []

            for mod in modules:
                name = mod.name

                for mod_name in module_names:
                    if mod_name == name:
                        tmp.append(mod)

                    elif "*" in mod_name:
                        name_regex = fnmatch.translate(mod_name)
                        reobj = re.compile(name_regex)
                        matches = [m.group(0) for module in modules for m in [reobj.search(module.name)] if m]
                        for match in matches:
                            if (match not in module_names):
                                module_names.append(match)
            modules = tmp

        return modules


    def _parse_version_or_release(self, keywords, keyword):
        """
        Parse the version or release for all the modules in the database
       
        :param keywords: dictionary of keywords to search for
        :param keyword: keyword to search for. (This value is either 'release' or 'version')
        """
        modules = []
        inequality = keywords[keyword][0]
        mmd_value = keywords[keyword][1]

        for name, mods in self.mods.items():
            for mod in mods:
                modules = self._get_modules_by_inequality(keyword, inequality, mmd_value, modules, mod)

        return modules

    def _get_modules_by_inequality(self, keyword, inequality, mmd_value, modules, mod):
        """
        Checks the inequality input for 'release' or 'version'

        :param keyword: keyword to check for. (This value is either 'release' or 'version')
        :param inequality: the inequality you want to check for (e.g., '<', '>', '==', etc)
        :param mmd_value: value for either 'release' or 'version'
        :param modules: list of modules
        :param mod: module you want to check for
        """

        #Select module metadata value
        if keyword == "_version":
            mmd = mod.mmd.version
        else:
            mmd = mod.mmd.release

        #Handle wildcards, if necessary
        if "*" in mmd_value:
            mmd_value_regex = fnmatch.translate(mmd_value)
            reobj = re.compile(mmd_value_regex)
            result = reobj.match(mmd)

            if result:
                mmd_value = result.string
            else:
                return modules

        #Parse inequality
        if (inequality == "=="):
            if (mmd == mmd_value):
                 modules.append(mod)
        elif (inequality == ">="):
            if (mmd >= mmd_value):
                modules.append(mod)
        elif (inequality == "<="):
            if (mmd <= mmd_value):
                modules.append(mod)
        elif (inequality == "<"):
            if (mmd < mmd_value):
                modules.append(mod)
        elif (inequality == ">"):
            if (mmd > mmd_value):
                modules.append(mod)
        elif (inequality == "!="):
            if (mmd != mmd_value):
                modules.append(mod)
        return modules


    def _check_for_wildcards_in_name(self, keywords):
        """
        For a given list of module names, check if there are wildcard
        """
        wildcards = False

        if "_name" not in keywords:
            return wildcards

        for mod_name in keywords["_name"]:
            if "*" in mod_name:
                wildcards = True
                break

        return wildcards
