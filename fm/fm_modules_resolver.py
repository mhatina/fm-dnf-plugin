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

from modulemd_resolver import ModulesResolver
import fm.exceptions
from fm.metadata_cache import CachedModuleMetadata

class FmModulesResolver(ModulesResolver):
    """
    ModulesResolver subclass providing Modules dependencies resolving
    and does the enablement/disablement/upgrade/downgrade of modules.
    """

    def __init__(self, mods, operator = "=="):
        """
        Creates new FmModulesResolver instance.
        """
        ModulesResolver.__init__(self)
        self.set_default_requires_operator(operator)

        #: Modules object instance
        self.mods = mods

        # Populate the ModulesResolver with the current state of modules
        # metadata on the system.
        for name, mods in mods.items():
            for mod in mods:
                if mod.is_enabled() and self.mods.enabled_cache.is_cached(mod):
                    self.add_enabled_mmd(mod.mmd)
                else:
                    self.add_available_mmd(mod.mmd)

        self._original_arg = None
        self.action = None

    def _edit_required_modules(self, mod, processed_modules, edit_fnc):
        """
        Iterates over the modules required by the processed and enabled
        modules during the modules enablement or disablement and executes
        `edit_fnc(required_module, mod.name)` for all the required modules.
        """
        for required_mod_name, version in mod.mmd.requires.items():
            required_mod = None

            # Try to find out the particular version of the depending
            # module we are going to enable together with this one.
            for mmd in processed_modules:
                if mmd.name == required_mod_name:
                    required_mod = self.mods.get_modules(mmd.name, mmd.version, mmd.release)[0]
                    break

            # If we did not find module in previous step, it means
            # that this module is already enabled on the system, so
            # try to find it out in the list of enabled modules.
            if not required_mod:
                for m in self.mods[required_mod_name]:
                    if m.is_enabled() and self.mods.enabled_cache.is_cached(m):
                        required_mod = m
                        break

            if not required_mod:
                raise fm.exceptions.DependencyError("Dependency on module {} is not satisfied.".format(required_mod_name))

            edit_fnc(required_mod, mod.name)

    def _enable_modules(self, modules, no_dnf = None, profiles = ["default"]):
        """
        Enables the modules defined by the `modules` list.
        """

        for mmd in modules:
            name = mmd.name
            # Check if we have some metadata for this module.
            if not name in self.mods:
                raise fm.exceptions.DependencyError("Dependency on module {} is not satisfied.".format(name))

            # Get the Module instance for this ModuleMetadata object.
            mods = self.mods.get_modules(mmd.name, mmd.version, mmd.release)
            if not mods:
                raise fm.exceptions.DependencyError("There is no module named {}".format(name))

            mod = mods[0]
            if not mod.mmd:
                raise fm.exceptions.DependencyError("There is no metadata associated with module {}".format(name))

            print("Enabling module", name + "-" + mod.mmd.version + "-" + mod.mmd.release)

            # Enable current module.
            if no_dnf == None:
                no_dnf = self.mods.opts.no_dnf
            mod.enable(profiles, not no_dnf)

            # Add this module as depending module for all the modules
            # this one required.
            if mod.mmd.requires:
                self._edit_required_modules(mod, modules,
                                            self.mods.enabled_cache.add_depending_mod)

            # Add this module to cache of enabled modules.
            self.mods.enabled_cache.store(mod,
                                          enabled_by_user = mod.name == self._original_arg)

    def _disable_modules(self, modules, no_dnf = None):
        """
        Disables the modules defined by the `modules` list.
        """

        for mmd in modules:
            name = mmd.name
            # Get the Module instance for this ModuleMetadata object.
            mods = self.mods.get_modules(mmd.name, mmd.version, mmd.release)
            if not mods:
                raise fm.exceptions.DependencyError("There is no module named {}".format(name))

            mod = mods[0]
            if not mod.mmd:
                raise fm.exceptions.DependencyError("There is no metadata associated with module {}".format(name))

            if not mod.is_enabled():
                continue

            print("Disabling module", name + "-" + mod.mmd.version + "-" + mod.mmd.release)

            # Now when all the depending modules are disabled, disable also
            # the original module.
            if no_dnf == None:
                no_dnf = self.mods.opts.no_dnf
            mod.disable(not no_dnf)

            # Remove this module as depending module for all the modules
            # this one required.
            self._edit_required_modules(mod, modules,
                                        self.mods.enabled_cache.remove_depending_mod)

            # Disable all modules this one required when they have not been enabled
            # by the user and there are no dependencies on them.
            def _disable_modules_wrapper(mod, name):
                if ((CachedModuleMetadata.ENABLED_BY_USER in mod.mmd.xmd
                        and mod.mmd.xmd[CachedModuleMetadata.ENABLED_BY_USER])):
                    return
                if len(self.mods.enabled_cache.get_depending_mods(mod)) != 0:
                    return
                self._disable_modules([mod.mmd])
            if self.action == "disable":
                self._edit_required_modules(mod, modules, _disable_modules_wrapper)

            self.mods.enabled_cache.remove(mod)

    def _upgrade_modules(self, modules, no_dnf = None, profiles = ["default"]):
        """
        Upgrades the modules defined by the `modules` list to latest version.
        """

        for from_mmd, to_mmd in modules:
            name = from_mmd.name
            print("Upgrading module",
                  name + "-" + from_mmd.version + "-" + from_mmd.release,
                  "to", name + "-" + to_mmd.version + "-" + to_mmd.release)

            self._disable_modules([from_mmd], True)
            try:
                self._enable_modules([to_mmd], profiles = profiles)
            except:
                self._enable_modules([from_mmd], True, profiles = profiles)
                raise
            mod = self.mods.get_modules(to_mmd.name, to_mmd.version, to_mmd.release)[0]
            mod.upgrade(not self.mods.opts.no_dnf)

    def _apply_result(self, ret, profiles = ["default"]):
        """
        Applies the results of the resolving - enables, disables, upgrades or
        downgrades the modules according to the resolving result.
        """
        self._enable_modules(ret.to_enable, profiles = profiles)
        self._disable_modules(ret.to_disable)
        self._upgrade_modules(ret.to_upgrade, profiles = profiles)
        self._upgrade_modules(ret.to_downgrade, profiles = profiles)
        if fm.api_clients.DNFBASE.dnfbase.sack \
                and not fm.api_clients.DNFBASE.pluginbase:
            fm.api_clients.DNFBASE.transaction_run()

    def execute(self, action, arg, profiles = ["default"]):
        """
        Executes the resolving action and applies the results. When this
        method returns, the `action` should be performed and modules should
        be enabled, disabled or upgraded accordingly. This method can ask
        users questions and expect input from stdin.
        """
        self._original_arg = arg
        self.action = action

        #: List of resolving solutions when some problem appears.
        solutions = []

        while True: 
            if action == "enable":
                ret = self.solve_enable(arg, solutions)
            elif action == "disable":
                ret = self.solve_disable(arg, solutions)
            elif action == "upgrade":
                ret = self.solve_update(arg, solutions)
            else:
                raise fm.exceptions.DependencyError("Unknown internal solvable action: " + action)

            if not ret:
                raise fm.exceptions.DependencyError("No such module: " + arg)

            if len(ret.problems) == 0:
                break

            #TODO: This should be forced by -y argument, by default we should
            # ask user.
            solution_size = len(solutions)
            for problem in ret.problems:
                if len(problem.solutions) > 0:
                    solutions += problem.solutions[0].solution

            # No solution found
            if solution_size == len(solutions):
                raise fm.exceptions.DependencyError(ret.problems[0].desc)

        self._apply_result(ret, profiles)
