import unittest

import ssl
from http.client import HTTPConnection

from verktyg_server import make_socket
from verktyg_server.testing import TestServer


class TestServerTestCase(unittest.TestCase):
    def test_basic(self):
        def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            return [b'hello world']

        with TestServer(application) as server:
            client = HTTPConnection('localhost', server.port)

            client.request('GET', '/')
            resp = client.getresponse()
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b'hello world')

            port = server.port

        # make sure server is down after leaving context
        self.assertRaises(ConnectionRefusedError, client.request, 'GET', '/')
        make_socket('localhost', port).close()
