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

from verktyg_server import make_socket, make_server
from verktyg_server.testing import choose_port


class ServingTestCase(unittest.TestCase):
    def test_basic(self):
        def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            return [b"Hello world!"]

        port = choose_port('localhost')

        server = make_server(make_socket('localhost', port), application)
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
