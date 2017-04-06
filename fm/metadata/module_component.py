# coding=utf-8
# Copyright (c) 2016-2017  Red Hat, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Written by Petr Šabata <contyk@redhat.com>
#            Jan Kaluza
#            Martin Hatina <mhatina@redhat.com>


supported_content = ( "rpms", "modules", )


class ModuleComponentBase(object):
    """A base class for definining module component types."""
    def __init__(self, name, rationale, buildorder=0):
        """Creates a new ModuleComponentBase instance."""
        self._name = name
        self._rationale = rationale
        self._buildorder = buildorder

    def __repr__(self):
        return "<ModuleComponentBase: name: {}, rationale: {}, buildorder: {}>" \
            .format(repr(self.name),
                    repr(self.rationale),
                    repr(self.buildorder))

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, s):
        if not isinstance(s, str):
            raise TypeError("componentbase.name: data type not supported")
        self._name = s

    @property
    def rationale(self):
        return self._rationale

    @rationale.setter
    def rationale(self, s):
        if not isinstance(s, str):
            raise TypeError("componentbase.rationale: data type not supported")
        self._rationale = s

    @property
    def buildorder(self):
        return self._buildorder

    @buildorder.setter
    def buildorder(self, i):
        if not isinstance(i, int):
            raise TypeError("componentbase.buildorder: data type not supported")
        self._buildorder = i


class ModuleComponentModule(ModuleComponentBase):
    """A component class for handling module-type content."""

    def __init__(self, name, rationale, buildorder=0, repository="", ref=""):
        super(ModuleComponentModule, self).__init__(name, rationale, buildorder)
        self._repository = repository
        self._ref = ref

    def __repr__(self):
        return "<ModuleComponentModule: name: {}, rationale: {}, buildorder: {}, " \
                "repository: {}, ref: {}>".format(repr(self.name), repr(self.rationale),
                                                  repr(self.buildorder), repr(self.repository),
                                                  repr(self.ref))

    @property
    def repository(self):
        return self._repository

    @repository.setter
    def repository(self, s):
        if not isinstance(s, str):
            raise TypeError("componentmodule.repository: data type not supported")
        self._repository = s

    @property
    def ref(self):
        return self._ref

    @ref.setter
    def ref(self, s):
        if not isinstance(s, str):
            raise TypeError("componentmodule.ref: data type not supported")
        self._ref = s


class ModuleComponentRPM(ModuleComponentBase):
    """A component class for handling RPM content."""
    def __init__(self, name, rationale, buildorder=0, repository="", ref="", cache="",
                 arches=set(), multilib=set()):
        super(ModuleComponentRPM, self).__init__(name, rationale, buildorder)
        self._repository = repository
        self._ref = ref
        self._cache = cache
        self._arches = arches
        self._multilib = multilib

    def __repr__(self):
        return "<ModuleComponentRPM: name: {}, rationale: {}, buildorder: {}, repository: {}, " \
                "ref: {}, cache: {}, arches: {}, multilib: {7}>" \
                .format(repr(self.name), repr(self.rationale), repr(self.buildorder),
                        repr(self.repository), repr(self.ref), repr(self.cache),
                        repr(sorted(self.arches)), repr(sorted(self.multilib)))

    @property
    def repository(self):
        return self._repository

    @repository.setter
    def repository(self, s):
        if not isinstance(s, str):
            raise TypeError("componentrpm.repository: data type not supported")
        self._repository = s

    @property
    def ref(self):
        return self._ref

    @ref.setter
    def ref(self, s):
        if not isinstance(s, str):
            raise TypeError("componentrpm.ref: data type not supported")
        self._ref = s

    @property
    def cache(self):
        return self._cache

    @cache.setter
    def cache(self, s):
        if not isinstance(s, str):
            raise TypeError("componentrpm.cache: data type not supported")
        self._cache = s

    @property
    def arches(self):
        return self._arches

    @arches.setter
    def arches(self, ss):
        if not isinstance(ss, set):
            raise TypeError("componentrpm.arches: data type not supported")
        for v in ss:
            if not isinstance(v, str):
                raise TypeError("componentrpm.arches: data type not supported")
        self._arches = ss

    @property
    def multilib(self):
        return self._multilib

    @multilib.setter
    def multilib(self, ss):
        if not isinstance(ss, set):
            raise TypeError("componentrpm.multilib: data type not supported")
        for v in ss:
            if not isinstance(v, str):
                raise TypeError("componentrpm.multilib: data type not supported")
        self._multilib = ss


class ModuleComponents(object):
    """Class representing components of a module."""
    def __init__(self):
        self._modules = dict()
        self._rpms = dict()

    def __repr__(self):
        return "<ModuleComponents: modules: {}, rpms: {}>".format(repr(sorted(self.modules)),
                                                                  repr(sorted(self.rpms)))

    @property
    def all(self):
        """Returns all the components regardless of their content type."""
        ac = list()
        ac.extend(self.rpms.values())
        ac.extend(self.modules.values())
        return ac

    @property
    def rpms(self):
        """A dictionary of RPM components in this module.  The keys are SRPM
        names, the values ModuleComponentRPM instances.
        """
        return self._rpms

    @rpms.setter
    def rpms(self, d):
        if not isinstance(d, dict):
            raise TypeError("components.rpms: data type not supported")
        for k, v in d.items():
            if not isinstance(k, str) or not isinstance(v, ModuleComponentRPM):
                raise TypeError("components.rpms: data type not supported")
        self._rpms = d

    def add_rpm(self, name, rationale, buildorder=0,
            repository="", ref="", cache="", arches=set(), multilib=set()):
        """Adds an RPM to the set of module components."""
        component = ModuleComponentRPM(name, rationale)
        component.buildorder = buildorder
        component.repository = repository
        component.ref = ref
        component.cache = cache
        component.arches = arches
        component.multilib = multilib
        self._rpms[name] = component

    def del_rpm(self, s):
        """Removes the supplied RPM from the set of module components."""
        if not isinstance(s, str):
            raise TypeError("components.del_rpm: data type not supported")
        if s in self._rpms:
            del self._rpms[s]

    def clear_rpms(self):
        """Clear the RPM component dictionary."""
        self._rpms.clear()

    @property
    def modules(self):
        """A dictionary of module-type components in this module.  The keys are
        module names, the values ModuleComponentModule instances.
        """
        return self._modules

    @modules.setter
    def modules(self, d):
        if not isinstance(d, dict):
            raise TypeError("components.modules: data type not supported")
        for k, v in d.items():
            if not isinstance(k, str) or not isinstance(v, ModuleComponentModule):
                raise TypeError("components.modules: data type not supported")
        self._modules = d

    def add_module(self, name, rationale, buildorder=0,
            repository="", ref=""):
        component = ModuleComponentModule(name, rationale)
        component.buildorder = buildorder
        component.repository = repository
        component.ref = ref
        self._modules[name] = component

    def del_module(self, s):
        """Removes the supplied module from the set of module components."""
        if not isinstance(s, str):
            raise TypeError("components.del_module: data type not supported")
        if s in self._modules:
            del self._modules[s]

    def clear_modules(self):
        """Clear the module-type component dictionary."""
        self._modules.clear()
