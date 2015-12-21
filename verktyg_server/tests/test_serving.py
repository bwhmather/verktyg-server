"""
    verktyg_server.tests.test_serving
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import unittest

from http.client import HTTPConnection
from threading import Thread

from verktyg_server import make_inet_socket, make_server

import logging
logging.disable(logging.CRITICAL)


class ServingTestCase(unittest.TestCase):
    def test_basic(self):
        def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            return [b"Hello world!"]

        socket = make_inet_socket('localhost')
        port = socket.getsockname()[1]

        server = make_server(socket, application)
        thread = Thread(target=server.serve_forever)
        thread.start()

        try:
            conn = HTTPConnection('localhost', port)
            conn.request('GET', '/')

            resp = conn.getresponse()
            self.assertEqual(resp.read(), b"Hello world!")
        finally:
            server.shutdown()
            thread.join()

    def test_yield_no_set_headers(self):
        def application(environ, start_response):
            return [b"Who needs headers"]

        socket = make_inet_socket('localhost')
        port = socket.getsockname()[1]

        server = make_server(socket, application)
        thread = Thread(target=server.serve_forever)
        thread.start()

        try:
            conn = HTTPConnection('localhost', port)
            conn.request('GET', '/')

            resp = conn.getresponse()
            self.assertEqual(resp.status, 500)
        finally:
            server.shutdown()
            thread.join()
