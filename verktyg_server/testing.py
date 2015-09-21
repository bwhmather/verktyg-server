"""
    verktyg_server.testing
    ~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
from threading import Thread

from verktyg_server import make_server, make_socket


class TestServer(object):
    def __init__(
                self, app, *, threaded=False,
                request_handler=None, ssl_context=None
            ):
        self._app = app
        self._threaded = threaded
        self._request_handler = request_handler
        self._ssl_context = ssl_context

    @property
    def protocol(self):
        return 'https' if self._ssl_context else 'http'

    @property
    def address(self):
        return '%s://%s:%s/' % (self.protocol, self.host, self.port)

    def __enter__(self):
        self.host = 'localhost'

        socket = make_socket(self.host, 0, ssl_context=self._ssl_context)
        self.port = socket.getsockname()[1]

        self._server = make_server(
            socket, self._app,
            threaded=self._threaded,
            request_handler=self._request_handler,
        )

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.start()

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._server.shutdown()
        self._thread.join()
