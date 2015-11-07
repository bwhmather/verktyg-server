"""
    verktyg_server.testing
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
from threading import Thread

from verktyg_server import make_server, make_inet_socket


class TestServer(object):
    def __init__(
                self, app, *, threaded=False,
                request_handler=None, ssl_context=None
            ):
        self._app = app
        self._threaded = threaded
        self._request_handler = request_handler
        self._ssl_context = ssl_context

        self._host = 'localhost'

        socket = make_inet_socket(self.host, 0, ssl_context=self._ssl_context)
        self._port = socket.getsockname()[1]

        self._server = make_server(
            socket, self._app,
            threaded=self._threaded,
            request_handler=self._request_handler,
        )

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.start()

        self.closed = False

    def close(self):
        self.closed = True
        self._server.shutdown()
        self._thread.join()

    @property
    def protocol(self):
        return 'https' if self._ssl_context else 'http'

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def address(self):
        return '%s://%s:%s/' % (self.protocol, self.host, self.port)

    def __enter__(self):
        if self.closed:
            raise ValueError("Cannot enter context with closed server")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
