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

import modulemd
import fm.exceptions
from fm.module import Module
from fm.modules import Modules
import json
import zlib

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

try:
    import http.client as httpclient
except ImportError:
    import httplib as httpclient

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from xml.etree import cElementTree as ET

class APIClient(object):
    """ Abstract API client class to be inherited by real client classes. """

    def __init__(self):
        #: Raw data received by last API call.
        self.raw_data = ""

    def get_raw_data(self):
        """
        Returns raw data received by the last API call.

        :return: Raw data.
        :rtype: string
        """
        return self.raw_data

    def list_modules(self):
        """
        Lists the available modules.

        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        :raises fm.exceptions.APICallError: If the YAML cannot be retrieved or parsed.
        """
        raise fm.exceptions.APICallError("This APICall is not implemented yet")

    def info_modules(self, arg):
        """
        Returns detail information about module.

        :param string arg: Name of the module for which the info is returned.
        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        :raises fm.exceptions.APICallError: If the YAML cannot be retrieved or parsed.
        """
        raise fm.exceptions.APICallError("This APICall is not implemented yet")

    def download(self, url):
        """
        Downloads the file from URL and returns it as a string.

        :param string url: URL.
        :return: Content of the file.
        :rtype: string
        :raises fm.exceptions.APICallError: If the file on URL cannot be retrieved.
        """
        if url.startswith("file://"):
            f = open(url[len("file://"):], "rb")
            self.raw_data = f.read()
            f.close()
            return self.raw_data

        parsed_url = urlparse(url)
        conn = httpclient.HTTPConnection(parsed_url.netloc)
        conn.request("GET", parsed_url.path)
        resp = conn.getresponse()

        if resp.status != 200:
            raise fm.exceptions.APICallError(
                'Received error from "{}": {} {}.'.format(
                    url, resp.status, resp.reason))

        self.raw_data = resp.read()
        return self.raw_data

class URLAPIClient(APIClient):
    """
    APIClient subclass getting metadata from file defined by URL.
    """
    def __init__(self, repo_cfg, repo_name, cfg, opts, api_clients):
        APIClient.__init__(self)
        self.repo_cfg = repo_cfg
        self.repo_name = repo_name
        self.cfg = cfg
        self.opts = opts
        self.api_clients = api_clients
        self.url = self.repo_cfg.get(repo_name, "url")
        self.metadata_expire = self.repo_cfg.get_metadata_expire(repo_name)

    def get_metadata_expire(self):
        """
        Returns time in seconds after which the metadata downloaded using
        this APIClient should expire.
        """
        return self.metadata_expire

    def get_modules_list(self, modules = []):
        """
        Calls API method. Returns response as a JSON object.

        :param string method: Name of the API method.
        :param string arg: Argument to be used for the API call.
        :return: JSON object.
        :rtype: json
        :raises fm.exceptions.APICallError: If the JSON cannot be retrieved or parsed.
        """

        url = self.url + "/modules.json"

        try:
            self.raw_data = self.download(url)
        except IOError as err:
                raise fm.exceptions.APICallError(
                    'Cannot find "{}" file: {}.'.format(url, err))

        try:
            if isinstance(self.raw_data, str):
                obj = json.loads(self.raw_data)
            else:
                obj = json.loads(self.raw_data.decode("utf-8"))
        except ValueError as err:
            raise fm.exceptions.APICallError(
                'Cannot parse "{}" response: {}.'.format(
                    url, err))

        # Check for error response.
        if isinstance(obj, dict) and "error" in obj:
            raise fm.exceptions.APICallError(
                '"list": {}.'.format(obj["error"]))

        return obj

    def parse_json_list_response(self, json_data):
        """
        Parses the list of modules received from metadata service.

        :param JSON json_data: JSON list with modules.
        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        """
        if not isinstance(json_data, list):
            raise fm.exceptions.APICallError('List of modules not received from server')

        # Fill in mods Modules object and return it.
        mods = Modules(self.cfg, self.opts, self.api_clients)
        #TODO: Sort json_data
        for mod in json_data:
            # Load the modulemd object from the response, or create
            # it when it is not part of the reponse.
            mmd = modulemd.ModuleMetadata()
            if "modulemd" in mod:
                try:
                    mmd.loads(mod["modulemd"])
                except ValueError as err:
                    raise fm.exceptions.APICallError(
                        'YAML document is not valid Module description: {}.'.format(err))
            else:
                mmd.name = mod["name"]
                mmd.summary = mod["summary"]
                mmd.version = mod["version"]
                mmd.release = mod["release"]

                for req_name, req_ver in mod["requires"].items():
                    mmd.update_requires(req_name, req_ver)

                mmd.xmd["_fm_need_refetch"] = True

            if "url" in mod:
                url = mod["url"]
                if url.find("://") == -1:
                    url = self.url + "/" + url
            else:
                url = self.url + "/" + mod["name"]
            mods.add_module(Module(self, mod["name"], url, mmd, self.opts.root))

        return mods

    def list_modules(self):
        """
        Lists the available modules.

        :return: {module_name: metadata, ...} dictionary
        :rtype: dict
        :raises fm.exceptions.APICallError: If the YAML cannot be retrieved or parsed.
        """
        json_data = self.get_modules_list()

        if not json_data:
            raise fm.exceptions.APICallError('No modules available')

        return self.parse_json_list_response(json_data)

    def get_module_metadata(self, url):
        """
        Downloads and returns module metadata from the repository.

        :return: Module metadata
        :rtype: modulemd object
        :raises fm.exceptions.APICallError: If the metadata cannot be retrieved or parsed.
        """

        self.raw_data = None
        try:
            self.raw_data = self.download(url + "/modulemd.yaml")
        except IOError as err:
            pass
        except fm.exceptions.APICallError as err:
            pass

        if not self.raw_data:
            try:
                repomd = self.download(url + "/repodata/repomd.xml")
            except IOError as err:
                raise fm.exceptions.APICallError('Cannot fetch module metadata: {}'.format(url))

            mmd_location = None
            tree = ET.XML(repomd)
            for data in tree:
                if not "type" in data.attrib or data.attrib["type"] != "module":
                    continue
                for location in data:
                    if location.tag.find("location") != -1:
                        mmd_location = location.attrib["href"]

            try:
                self.raw_data = self.download(url + "/" + mmd_location)
            except IOError as err:
                raise fm.exceptions.APICallError('Cannot fetch module metadata: {}'.format(url))

            if mmd_location.endswith(".gz"):
                self.raw_data = zlib.decompress(self.raw_data, 16+zlib.MAX_WBITS)

        mmd = modulemd.ModuleMetadata()
        try:
            mmd.loads(self.raw_data)
        except ValueError as err:
            raise fm.exceptions.APICallError(
                'YAML document is not valid Module description: {}.'.format(err))
        return mmd
