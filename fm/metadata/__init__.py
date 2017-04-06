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

import yaml
import os
import gzip

import fm
from fm.metadata.module_api import ModuleAPI
from fm.metadata.module_component import ModuleComponents
from fm.metadata.module_filter import ModuleFilter
from fm.metadata.module_profile import ModuleProfile

supported_mdversions = (1, )


class ModuleMetadata(object):
    def __init__(self, repo):
        self.repo = repo

        self._mdversion = max(supported_mdversions)
        self._name = ""
        self._stream = ""
        self._version = 0
        self._summary = ""
        self._description = ""
        self._licenses = set()
        self._requires = dict()
        self._buildrequires = dict()
        self._community = ""
        self._documentation = ""
        self._tracker = ""
        self._xmd = dict()
        self._profiles = dict()
        self._api = ModuleAPI()
        self._components = None
        self._filter = ModuleFilter()
        self._dependencies = ""

    def is_enabled(self):
        return self._name in fm.dnfbase.base.conf.enabled_modules

    def get_nvr(self):
        return "{}-{}".format(self._name, self._version)

    def load(self, parsed_yaml):
        self.check_required_items(parsed_yaml)
        self.mdversion = parsed_yaml["version"]
        parsed_yaml = parsed_yaml["data"]

        if "name" in parsed_yaml:
            self.name = str(parsed_yaml["name"]).strip()

        if "stream" in parsed_yaml:
            self.stream = str(parsed_yaml["stream"]).strip()

        if "version" in parsed_yaml:
            self.version = int(parsed_yaml["version"])

        if "summary" in parsed_yaml:
            self.summary = str(parsed_yaml["summary"]).strip()

        if "description" in parsed_yaml:
            self.description = str(parsed_yaml["description"]).strip()

        if "license" in parsed_yaml \
                and isinstance(parsed_yaml["license"], dict) \
                and "module" in parsed_yaml["license"] \
                and parsed_yaml["license"]["module"]:
            self.licenses = set(parsed_yaml["license"]["module"])

        if "dependencies" in parsed_yaml and isinstance(parsed_yaml["dependencies"], dict):
            if "buildrequires" in parsed_yaml["dependencies"] \
                    and isinstance(parsed_yaml["dependencies"]["buildrequires"], dict):
                for n, s in parsed_yaml["dependencies"]["buildrequires"].items():
                    self.buildrequires[str(n)] = str(s)

            if "requires" in parsed_yaml["dependencies"] \
                    and isinstance(parsed_yaml["dependencies"]["requires"], dict):
                for n, s in parsed_yaml["dependencies"]["requires"].items():
                    self.requires[str(n)] = str(s)

        if "references" in parsed_yaml and parsed_yaml["references"]:
            if "community" in parsed_yaml["references"]:
                self.community = parsed_yaml["references"]["community"]
            if "documentation" in parsed_yaml["references"]:
                self.documentation = parsed_yaml["references"]["documentation"]
            if "tracker" in parsed_yaml["references"]:
                self.tracker = parsed_yaml["references"]["tracker"]

        if "xmd" in parsed_yaml:
            self.xmd = parsed_yaml["xmd"]

        if "profiles" in parsed_yaml \
                and isinstance(parsed_yaml["profiles"], dict):
            for profile in parsed_yaml["profiles"].keys():
                self.profiles[profile] = ModuleProfile()
                if "description" in parsed_yaml["profiles"][profile]:
                    self.profiles[profile].description = \
                        str(parsed_yaml["profiles"][profile]["description"])
                if "rpms" in parsed_yaml["profiles"][profile]:
                    self.profiles[profile].rpms = \
                        set(parsed_yaml["profiles"][profile]["rpms"])

        if "api" in parsed_yaml \
                and isinstance(parsed_yaml["api"], dict):
            self._api = ModuleAPI()
            if "rpms" in parsed_yaml["api"] \
                    and isinstance(parsed_yaml["api"]["rpms"], list):
                self._api.rpms = set(parsed_yaml["api"]["rpms"])

        if "filter" in parsed_yaml \
                and isinstance(parsed_yaml["filter"], dict):
            self._filter = ModuleFilter()
            if "rpms" in parsed_yaml["filter"] \
                    and isinstance(parsed_yaml["filter"]["rpms"], list):
                self._filter.rpms = set(parsed_yaml["filter"]["rpms"])

        if "components" in parsed_yaml \
                and isinstance(parsed_yaml["components"], dict):
            self._components = ModuleComponents()
            if "rpms" in parsed_yaml["components"]:
                for p, e in parsed_yaml["components"]["rpms"].items():
                    extras = dict()
                    extras["rationale"] = e["rationale"]
                    if "buildorder" in e:
                        extras["buildorder"] = int(e["buildorder"])
                    if "repository" in e:
                        extras["repository"] = str(e["repository"])
                    if "cache" in e:
                        extras["cache"] = str(e["cache"])
                    if "ref" in e:
                        extras["ref"] = str(e["ref"])
                    if "arches" in e \
                            and isinstance(e["arches"], list):
                        extras["arches"] = set(str(x) for x in e["arches"])
                    if "multilib" in e \
                            and isinstance(e["multilib"], list):
                        extras["multilib"] = set(str(x) for x in e["multilib"])
                    self._components.add_rpm(p, **extras)
            if "modules" in parsed_yaml["components"]:
                for p, e in parsed_yaml["components"]["modules"].items():
                    extras = dict()
                    extras["rationale"] = e["rationale"]
                    if "buildorder" in e:
                        extras["buildorder"] = int(e["buildorder"])
                    if "repository" in e:
                        extras["repository"] = str(e["repository"])
                    if "ref" in e:
                        extras["ref"] = str(e["ref"])
                    self._components.add_module(p, **extras)

    @staticmethod
    def check_required_items(parsed_yaml):
        if "document" not in parsed_yaml or parsed_yaml["document"] != "modulemd":
            raise ValueError("The supplied data isn't a valid modulemd document")
        if "version" not in parsed_yaml:
            raise ValueError("Document version is required")
        if parsed_yaml["version"] not in supported_mdversions:
            raise ValueError("The supplied metadata version isn't supported")

    def dump_to_string(self):
        data = dict()
        # header
        data["document"] = "modulemd"
        data["version"] = self.mdversion
        # data
        data = dict()
        data["name"] = self.name
        data["stream"] = self.stream
        data["version"] = self.version
        data["summary"] = self.summary
        data["description"] = self.description
        data["license"] = dict()
        data["license"]["module"] = list(self.licenses)
        if self.buildrequires or self.requires:
            data["dependencies"] = dict()
            if self.buildrequires:
                data["dependencies"]["buildrequires"] = self.buildrequires
            if self.requires:
                data["dependencies"]["requires"] = self.requires
        if self.community or self.documentation or self.tracker:
            data["references"] = dict()
            if self.community:
                data["references"]["community"] = self.community
            if self.documentation:
                data["references"]["documentation"] = self.documentation
            if self.tracker:
                data["references"]["tracker"] = self.tracker
        if self.xmd:
            data["xmd"] = self.xmd
        if self.profiles:
            data["profiles"] = dict()
            for profile in self.profiles.keys():
                if self.profiles[profile].description:
                    if profile not in data["profiles"]:
                        data["profiles"][profile] = dict()
                    data["profiles"][profile]["description"] = \
                        str(self.profiles[profile].description)
                if self.profiles[profile].rpms:
                    if profile not in data["profiles"]:
                        data["profiles"][profile] = dict()
                    data["profiles"][profile]["rpms"] = \
                        list(self.profiles[profile].rpms)

        return yaml.safe_dump(data)

    @property
    def mdversion(self):
        return self._mdversion

    @mdversion.setter
    def mdversion(self, i):
        if not isinstance(i, int):
            raise TypeError("mdversion: data type not supported")
        if i not in supported_mdversions:
            raise ValueError("mdversion: document version not supported")
        self._mdversion = int(i)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, s):
        if not isinstance(s, str):
            raise TypeError("name: data type not supported")
        self._name = s

    @property
    def stream(self):
        """A string property representing the stream name of the module."""
        return self._stream

    @stream.setter
    def stream(self, s):
        if not isinstance(s, str):
            raise TypeError("stream: data type not supported")
        self._stream = str(s)

    @property
    def version(self):
        """An integer property representing the version of the module."""
        return self._version

    @version.setter
    def version(self, i):
        if not isinstance(i, int):
            raise TypeError("version: data type not supported")
        if i < 0:
            raise ValueError("version: version cannot be negative")
        self._version = i

    @property
    def summary(self):
        """A string property representing a short summary of the module."""
        return self._summary

    @summary.setter
    def summary(self, s):
        if not isinstance(s, str):
            raise TypeError("summary: data type not supported")
        self._summary = s

    @property
    def description(self):
        """A string property representing a detailed description of the
        module."""
        return self._description

    @description.setter
    def description(self, s):
        if not isinstance(s, str):
            raise TypeError("description: data type not supported")
        self._description = s

    @property
    def licenses(self):
        return self._licenses

    @licenses.setter
    def licenses(self, ss):
        if not isinstance(ss, set):
            raise TypeError("licenses: data type not supported")
        for s in ss:
            if not isinstance(s, str):
                raise TypeError("licenses: data type not supported")
        self._licenses = ss

    def add_license(self, s):
        if not isinstance(s, str):
            raise TypeError("add_license: data type not supported")
        self._licenses.add(s)

    def delete_license(self, s):
        if not isinstance(s, str):
            raise TypeError("delete_license: data type not supported")
        self._licenses.discard(s)

    def clear_licenses(self):
        self._licenses.clear()

    @property
    def requires(self):
        """A dictionary property representing the required dependencies of
        the module.
        Keys are the required module names (strings), values are their
        required stream names (also strings).
        """
        return self._requires

    @requires.setter
    def requires(self, d):
        if not isinstance(d, dict):
            raise TypeError("requires: data type not supported")
        for k, v in d.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise TypeError("requires: data type not supported")
        self._requires = d

    def add_requires(self, n, v):
        """Adds a required module dependency.
        :param str n: Required module name
        :param str v: Required module stream name
        """
        if not isinstance(n, str) or not isinstance(v, str):
            raise TypeError("add_requires: data type not supported")
        self._requires[n] = v

    update_requires = add_requires

    def delete_requires(self, n):
        """Deletes the dependency on the supplied module.
        :param str n: Required module name
        """
        if not isinstance(n, str):
            raise TypeError("delete_requires: data type not supported")
        if n in self._requires:
            del self._requires[n]

    def clear_requires(self):
        """Removes all required runtime dependencies."""
        self._requires.clear()

    @property
    def buildrequires(self):
        """A dictionary property representing the required build dependencies
        of the module.
        Keys are the required module names (strings), values are their
        required stream names (also strings).
        """
        return self._buildrequires

    @buildrequires.setter
    def buildrequires(self, d):
        if not isinstance(d, dict):
            raise TypeError("buildrequires: data type not supported")
        for k, v in d.items():
            if not isinstance(k, str) or not isinstance(v, str):
                raise TypeError("buildrequires: data type not supported")
        self._buildrequires = d

    def add_buildrequires(self, n, v):
        """Adds a module build dependency.
        :param str n: Required module name
        :param str v: Required module stream name
        """
        if not isinstance(n, str) or not isinstance(v, str):
            raise TypeError("add_buildrequires: data type not supported")
        self._buildrequires[n] = v

    update_buildrequires = add_buildrequires

    def delete_buildrequires(self, n):
        """Deletes the build dependency on the supplied module.
        :param str n: Required module name
        """
        if not isinstance(n, str):
            raise TypeError("delete_buildrequires: data type not supported")
        if n in self._buildrequires:
            del self._buildrequires[n]

    def clear_buildrequires(self):
        """Removes all build dependencies."""
        self._buildrequires.clear()

    @property
    def community(self):
        """A string property representing a link to the upstream community
        for this module.
        """
        return self._community

    @community.setter
    def community(self, s):
        # TODO: Check if it looks like a link, unless empty
        if not isinstance(s, str):
            raise TypeError("community: data type not supported")
        self._community = s

    @property
    def documentation(self):
        """A string property representing a link to the upstream
        documentation for this module.
        """
        return self._documentation

    @documentation.setter
    def documentation(self, s):
        # TODO: Check if it looks like a link, unless empty
        if not isinstance(s, str):
            raise TypeError("documentation: data type not supported")
        self._documentation = s

    @property
    def tracker(self):
        """A string property representing a link to the upstream bug tracker
        for this module.
        """
        return self._tracker

    @tracker.setter
    def tracker(self, s):
        # TODO: Check if it looks like a link, unless empty
        if not isinstance(s, str):
            raise TypeError("tracker: data type not supported")
        self._tracker = s

    @property
    def xmd(self):
        """A dictionary property containing user-defined data."""
        return self._xmd

    @xmd.setter
    def xmd(self, d):
        if not isinstance(d, dict):
            raise TypeError("xmd: data type not supported")
        self._xmd = d

    @property
    def profiles(self):
        """A dictionary property representing the module profiles."""
        return self._profiles

    @profiles.setter
    def profiles(self, d):
        if not isinstance(d, dict):
            raise TypeError("profiles: data type not supported")
        for k, v in d.items():
            if not isinstance(k, str) or not isinstance(v, ModuleProfile):
                raise TypeError("profiles: data type not supported")
        self._profiles = d


class ModuleMetadataLoader(object):
    def __init__(self, repo=None):
        self.repo = repo

    def load(self):
        if self.repo is None:
            raise Exception("Cannot load from cache dir: {}".format(self.repo))

        content_of_cachedir = os.listdir(self.repo._cachedir + "/repodata")
        modules_yaml_gz = list(filter(lambda repodata_file:'modules' in repodata_file,
                                      content_of_cachedir))

        if len(modules_yaml_gz) == 0:
            raise Exception("Missing file *modules.yaml in metadata cache dir: {}".format(self.repo._cachedir))
        modules_yaml_gz = "{}/repodata/{}".format(self.repo._cachedir, modules_yaml_gz[0])

        with gzip.open(modules_yaml_gz, "r") as extracted_modules_yaml_gz:
            modules_yaml = extracted_modules_yaml_gz.read()

        return self.parse_yaml(modules_yaml)

    def parse_yaml(self, raw_data):
        parsed_yaml = yaml.safe_load(raw_data)
        metadata = []
        for data in parsed_yaml["modules"]:
            module_data = ModuleMetadata(self.repo)
            module_data.load(data)
            metadata.append(module_data)

        return metadata
