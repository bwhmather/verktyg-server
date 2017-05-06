"""
    verktyg_server.tests.test_sockets
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2017 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import socket
import unittest

from verktyg_server import make_inet_socket


def _find_open_port(self, *, interface='localhost'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Disable re-use of the port by other processes to avoid race condition.
    # This won't prevent re-use of the socket by the current process.
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    sock.bind((interface, 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class InetSocketsTestCase(unittest.TestCase):
    def test_make_inet_socket_hostname(self):
        # TODO this is a bit racy.
        port = _find_open_port('localhost')

        # Call `make_inet_socket` to open a listening socket.
        sock = make_inet_socket('localhost', port=port)
        self.addCleanup(sock.close)

        # Check that basic socket attributes match what we would expect.
        actual_addr, actual_port = sock.getsockname()
        self.assertEqual(actual_addr, '127.0.0.1')
        self.assertEqual(actual_port, port)

        actual_timeout = sock.gettimeout()
        self.assertEqual(actual_timeout, None)

        self.assertEqual(sock.family, socket.AF_INET)
        self.assertEqual(sock.type, socket.SOCK_STREAM)
        self.assertEqual(sock.proto, 0)

        reuse_addr = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
        self.assertEqual(reuse_addr, 1)

        # Everything after here is us just us prodding the socket to make sure
        # that it behaves as expected.
        # Try to connect to it and send some stuff.
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addCleanup(client_sock.close)

        client_sock.connect(('127.0.0.1', port))
        client_sock.sendall(b'hello!')

        # Accept the incoming connection and read the data.
        sock.listen(1)
        server_conn, addr = sock.accept()
        self.addCleanup(server_conn.close)

        self.assertEqual(server_conn.recv(6), b'hello!')

    def test_make_inet_socket_ssl(self):
        pass

    def test_make_inet_socket_ipv6(self):
        # TODO this is a bit racy.
        port = _find_open_port('::1')

        # Call `make_inet_socket` to open a listening socket.
        sock = make_inet_socket('::1', port=port)
        self.addCleanup(sock.close)

        # Check that basic socket attributes match what we would expect.
        actual_addr, actual_port, _flow_info, _scope_id = sock.getsockname()
        self.assertEqual(actual_addr, '::1')
        self.assertEqual(actual_port, port)

        actual_timeout = sock.gettimeout()
        self.assertEqual(actual_timeout, None)

        self.assertEqual(sock.family, socket.AF_INET6)
        self.assertEqual(sock.type, socket.SOCK_STREAM)
        self.assertEqual(sock.proto, 0)

        reuse_addr = sock.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
        self.assertEqual(reuse_addr, 1)

        # Everything after here is us just us prodding the socket to make sure
        # that it behaves as expected.
        # Try to connect to it and send some stuff.
        client_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.addCleanup(client_sock.close)

        client_sock.connect(('::1', port))
        client_sock.sendall(b'hello!')

        # Accept the incoming connection and read the data.
        sock.listen(1)
        server_conn, addr = sock.accept()
        self.addCleanup(server_conn.close)

        self.assertEqual(server_conn.recv(6), b'hello!')
