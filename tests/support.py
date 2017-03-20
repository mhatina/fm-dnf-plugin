# Copyright (C) 2015-2016  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from __future__ import absolute_import
import os
import re
import unittest
import shutil
import socket
import threading
import errno

from fm.cli import Cli

try:
    import SocketServer
except:
    import socketserver as SocketServer

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        response = "HTTP/1.1 200 OK\nContent-Length:{}\n\n".format(len(self.response)) + self.response
        try:
            self.request.sendall(bytes(response, "UTF-8"))
        except TypeError:
            self.request.sendall(bytes(response))

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def start_server(response):
    HOST, PORT = "localhost", 0

    handler = ThreadedTCPRequestHandler
    handler.response = response
    server = ThreadedTCPServer((HOST, PORT), handler)
    #ip, port = server.server_address

    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    return server

def stop_server(server):
    server.shutdown()
    server.server_close()

class TestCase(unittest.TestCase):

    def assertEmpty(self, collection):
        return self.assertEqual(len(collection), 0)

    def assertFile(self, path):
        """Assert the given path is a file."""
        return self.assertTrue(os.path.isfile(path))

    def assertLength(self, collection, length):
        return self.assertEqual(len(collection), length)

    def assertPathDoesNotExist(self, path):
        return self.assertFalse(os.access(path, os.F_OK))

    def assertStartsWith(self, string, what):
        return self.assertTrue(string.startswith(what))

    def assertFind(self, string, what):
        return self.assertTrue(string.find(what) != -1)

    def assertNotFind(self, string, what):
        return self.assertTrue(string.find(what) == -1)

    def assertTracebackIn(self, end, string):
        """Test that a traceback ending with line *end* is in the *string*."""
        traces = (match.group() for match in TRACEBACK_RE.finditer(string))
        self.assertTrue(any(trace.endswith(end) for trace in traces))

    def setupServer(self, response):
        #self.server = start_server(response)
        #self.port = self.server.server_address[1]
        pass


    def setUp(self):
        #self.server = None
        #self.port = 0
        self.output = StringIO()
        self.cli = Cli(self.output)

        mkdir_p("./test.modules.d")
        mkdir_p("./test.cache.d")
        cfg = "[fm]\n"
        cfg += "modules_dir=./test.modules.d\n"
        cfg += "cache_dir=./test.cache.d\n"
        f = open(".test_main.cfg", "w")
        f.write(cfg)
        f.close()

        cfg = "[default]\nurl={}\n".format("file://" + os.getcwd() + "/test-repo")
        f = open("./test.modules.d/default.cfg", "w")
        f.write(cfg)
        f.close()

        mkdir_p("./test_root/etc/yum.repos.d")

    def tearDown(self):
        #if self.server:
            #stop_server(self.server)
        shutil.rmtree('./test_root')
        shutil.rmtree('./test.modules.d')
        shutil.rmtree('./test.cache.d')
        os.remove(".test_main.cfg")

    def params(self, args):
        return ["-r", "./test_root", '-c', './.test_main.cfg'] + args

