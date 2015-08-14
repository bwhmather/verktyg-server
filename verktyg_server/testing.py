"""
    verktyg_server.testing
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import socket
from threading import Thread

from verktyg_server import make_server, make_socket


def choose_port(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestServer(object):
    def __init__(
                self, app, *, threaded=False,
                request_handler=None, ssl_context=None
            ):
        self._app = app
        self._threaded = threaded
        self._request_handler = request_handler
        self._ssl_context = ssl_context

    def __enter__(self):
        self.host = 'localhost'
        self.port = choose_port(self.host)

        self._socket = make_socket(
            self.host, self.port, ssl_context=self._ssl_context
        )
        self._server = make_server(
            self._socket, self._app,
            threaded=self._threaded,
            request_handler=self._request_handler,
        )

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.start()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._server.shutdown()
        self._thread.join()
