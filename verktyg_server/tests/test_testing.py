import unittest

import ssl
from http.client import HTTPConnection, HTTPSConnection

from verktyg_server.sslutils import make_adhoc_ssl_context
from verktyg_server import make_inet_socket
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
        make_inet_socket('localhost', port).close()

    def test_ssl(self):
        def application(environ, start_response):
            status = '200 OK'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            return [b'hello ssl']

        server_ssl_context = make_adhoc_ssl_context()
        client_ssl_context = ssl._create_stdlib_context()  # TODO

        with TestServer(application, ssl_context=server_ssl_context) as server:
            client = HTTPSConnection(
                server.host, server.port, context=client_ssl_context
            )

            client.request('GET', '/')
            resp = client.getresponse()
            self.assertEqual(resp.status, 200)
