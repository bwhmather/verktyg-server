"""
    verktyg_server
    ~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import sys
import urllib.parse
import ssl
import socket
from socket import getfqdn
import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

import pkg_resources

from verktyg_server.sslutils import load_ssl_context, make_adhoc_ssl_context

import logging
log = logging.getLogger('verktyg_server')


__version__ = pkg_resources.get_distribution("verktyg-server").version


class WSGIRequestHandler(BaseHTTPRequestHandler, object):
    """A request handler that implements WSGI dispatching."""

    @property
    def server_version(self):
        return 'verktyg-server/' + __version__

    def make_environ(self):
        request_url = urllib.parse.urlparse(self.path)

        if request_url.scheme:
            url_scheme = request_url.scheme
        elif isinstance(self.server.socket, ssl.SSLSocket):
            url_scheme = 'https'
        else:
            url_scheme = 'http'

        path = urllib.parse.unquote_to_bytes(
            request_url.path
        ).decode('iso-8859-1')

        environ = {
            'wsgi.version':         (1, 0),
            'wsgi.url_scheme':      url_scheme,
            'wsgi.input':           self.rfile,
            'wsgi.errors':          sys.stderr,
            'wsgi.multithread':     self.server.multithread,
            'wsgi.multiprocess':    self.server.multiprocess,
            'wsgi.run_once':        False,
            'verktyg.server.shutdown': self.server.shutdown,
            'SERVER_SOFTWARE':      self.server_version,
            'REQUEST_METHOD':       self.command,
            'SCRIPT_NAME':          '',
            'PATH_INFO':            path,
            'QUERY_STRING':         request_url.query,
            'CONTENT_TYPE':         self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH':       self.headers.get('Content-Length', ''),
            'REMOTE_ADDR':          self.client_address[0],
            'REMOTE_PORT':          self.client_address[1],
            'SERVER_NAME':          self.server.server_address[0],
            'SERVER_PORT':          str(self.server.server_address[1]),
            'SERVER_PROTOCOL':      self.request_version
        }

        for key, value in self.headers.items():
            key = 'HTTP_' + key.upper().replace('-', '_')
            if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                environ[key] = value

        if request_url.netloc:
            environ['HTTP_HOST'] = request_url.netloc

        if hasattr(self.request, 'getpeercert'):
            environ['REMOTE_CERT'] = self.request.getpeercert(binary_form=True)

        return environ

    def run_wsgi(self):
        if self.headers.get('Expect', '').lower().strip() == '100-continue':
            self.wfile.write(b'HTTP/1.1 100 Continue\r\n\r\n')

        self.environ = environ = self.make_environ()
        headers_set = []
        headers_sent = []

        def write(data):
            assert headers_set, 'write() before start_response'
            if not headers_sent:
                status, response_headers = headers_sent[:] = headers_set
                try:
                    code, msg = status.split(None, 1)
                except ValueError:
                    code, msg = status, ""
                self.send_response(int(code), msg)
                header_keys = set()
                for key, value in response_headers:
                    self.send_header(key, value)
                    key = key.lower()
                    header_keys.add(key)
                if 'content-length' not in header_keys:
                    self.close_connection = True
                    self.send_header('Connection', 'close')
                if 'server' not in header_keys:
                    self.send_header('Server', self.version_string())
                if 'date' not in header_keys:
                    self.send_header('Date', self.date_time_string())
                self.end_headers()

            assert isinstance(data, bytes), 'applications must write bytes'
            self.wfile.write(data)
            self.wfile.flush()

        def start_response(status, response_headers, exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        exc_type, exc_value, exc_traceback = exc_info
                        if exc_value.__traceback__ is not exc_traceback:
                            raise exc_value.with_traceback(exc_traceback)
                        raise exc_value
                finally:
                    exc_info = None
            elif headers_set:
                raise AssertionError('Headers already set')
            headers_set[:] = [status, response_headers]
            return write

        def execute(app):
            application_iter = app(environ, start_response)
            try:
                for data in application_iter:
                    write(data)
                if not headers_sent:
                    write(b'')
            finally:
                if hasattr(application_iter, 'close'):
                    application_iter.close()
                application_iter = None

        try:
            execute(self.server.app)
        except (socket.error, socket.timeout) as e:
            self.connection_dropped(e, environ)
        except Exception as e:
            if self.server.passthrough_errors:
                raise
            self.logger.error("Error on request", exc_info=True)
            try:
                # if we haven't yet sent the headers but they are set
                # we roll back to be able to set them again.
                if not headers_sent:
                    del headers_set[:]
                execute(self.render_error)
            except Exception:
                self.logger.exception("error recovering from failed response")

    def render_error(self, environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/html')]
        start_response(status, headers)
        return [b"<h1>Internal Server Error</h1>"]

    def handle(self):
        """Handles a request ignoring dropped connections."""
        rv = None
        try:
            rv = BaseHTTPRequestHandler.handle(self)
        except (socket.error, socket.timeout, ssl.SSLError) as e:
            self.connection_dropped(e)
        return rv

    def connection_dropped(self, error, environ=None):
        """Called if the connection was closed by the client.  By default
        nothing happens.
        """

    def handle_one_request(self):
        """Handle a single HTTP request."""
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
        elif self.parse_request():
            return self.run_wsgi()

    def send_response(self, code, message=None):
        """Send the response header and log the response code."""
        self.log_request(code)
        if message is None:
            message = code in self.responses and self.responses[code][0] or ''
        if self.request_version != 'HTTP/0.9':
            hdr = "%s %d %s\r\n" % (self.protocol_version, code, message)
            self.wfile.write(hdr.encode('ascii'))

    def version_string(self):
        return BaseHTTPRequestHandler.version_string(self).strip()

    def address_string(self):
        return self.environ['REMOTE_ADDR']

    def log_request(self, code='-', size='-'):
        self.logger.info('%r %s %s', self.requestline, code, size)

    def log_error(self, *args):
        self.logger.error(format, *args)

    def log_message(self, format, *args):
        self.logger.info(format, *args)

    @property
    def logger(self):
        return self.server.logger


class BaseWSGIServer(HTTPServer, object):
    """Simple single-threaded, single-process WSGI server."""
    multithread = False
    multiprocess = False
    request_queue_size = 128

    def __init__(
                self, socket, app, *, handler=None,
                passthrough_errors=False, logger=None
            ):
        if logger is None:
            logger = 'verktyg-server'
        if isinstance(logger, str):
            logger = logging.getLogger(logger)
        self.logger = logger

        if handler is None:
            handler = WSGIRequestHandler

        self.socket = socket
        server_address = self.socket.getsockname()
        socketserver.BaseServer.__init__(self, server_address, handler)

        host, port = server_address[:2]
        self.server_name = getfqdn(host)
        self.server_port = port

        self.app = app
        self.passthrough_errors = passthrough_errors

    def log(self, type, message, *args):
        log.log(type, message, *args)

    def serve_forever(self):
        try:
            HTTPServer.serve_forever(self)
        except KeyboardInterrupt:
            pass
        finally:
            self.server_close()

    def handle_error(self, request, client_address):
        if self.passthrough_errors:
            raise
        else:
            return HTTPServer.handle_error(self, request, client_address)

    def get_request(self):
        con, info = self.socket.accept()
        return con, info


class ThreadedWSGIServer(socketserver.ThreadingMixIn, BaseWSGIServer):
    """A WSGI server that does threading."""
    multithread = True


class ForkingWSGIServer(socketserver.ForkingMixIn, BaseWSGIServer):
    """A WSGI server that does forking."""
    multiprocess = True

    def __init__(
                self, socket, app, *, processes=40, handler=None,
                passthrough_errors=False
            ):
        BaseWSGIServer.__init__(
            self, socket, app, handler=handler,
            passthrough_errors=passthrough_errors
        )
        self.max_children = processes


def make_server(
            socket, app=None, *, threaded=False, processes=1,
            request_handler=None, passthrough_errors=False
        ):
    """Create a new server instance listening on the given socket that is
    either threaded, or forks or just processes one request after another.
    """
    if threaded and processes > 1:
        raise TypeError(
            "cannot have a multithreaded and multi process server."
        )
    elif threaded:
        return ThreadedWSGIServer(
            socket, app, handler=request_handler,
            passthough_errors=passthrough_errors,
        )
    elif processes > 1:
        return ForkingWSGIServer(
            socket, app,  handler=request_handler,
            passthrough_errors=passthrough_errors,
            processes=processes
        )
    else:
        return BaseWSGIServer(
            socket, app, handler=request_handler,
            passthrough_errors=passthrough_errors
        )


def _is_ipv6_address(address):
    # TODO
    return ':' in address


def _wrap_ssl(sock, ssl_context):
    if isinstance(ssl_context, tuple):
        ssl_context = load_ssl_context(*ssl_context)
    if ssl_context == 'adhoc':
        ssl_context = make_adhoc_ssl_context()
    return ssl_context.wrap_socket(sock, server_side=True)


def make_inet_socket(interface, port=0, *, backlog=2048, ssl_context=None):
    if _is_ipv6_address(interface):
        family = socket.AF_INET6
    else:
        family = socket.AF_INET

    address = (interface, port)

    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(True)

    sock.bind(address)
    sock.listen(backlog)

    if ssl_context is not None:
        sock = _wrap_ssl(sock, ssl_context)

    return sock


def make_fd_socket(fd, *, family=socket.AF_UNIX, ssl_context=None):
    sock = socket.fromfd(fd, family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(True)

    if ssl_context is not None:
        sock = _wrap_ssl(sock, ssl_context)

    return sock


def make_unix_socket(filename, *, backlog=2048, ssl_context=None):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(True)

    sock.bind(filename)
    sock.listen(backlog)

    if ssl_context is not None:
        sock = _wrap_ssl(sock, ssl_context)

    return sock


def make_socket(address, ssl_context=None):
    components = urllib.parse.urlsplit(address)

    if components.scheme in {'http', 'https'}:
        host, port = components.netloc.split(':', 1)

        if port:
            port = int(port)
        else:
            port = {
                'http': 80,
                'https': 443,
            }[components.scheme]

        return make_inet_socket(host, port, ssl_context=ssl_context)
    elif components.scheme == 'fd':
        return make_fd_socket(int(components.netloc), ssl_context=ssl_context)
    elif components.scheme == 'unix':
        return make_unix_socket(components.path, ssl_context=ssl_context)


def main():
    import argparse
    import importlib
    import verktyg_server.argparse

    parser = argparse.ArgumentParser()

    verktyg_server.argparse.add_arguments(parser)

    parser.add_argument(
        'app_factory', metavar='FACTORY',
        help=(
            'module path of function to be called to generate wsgi '
            'application'
        )
    )

    args = parser.parse_args()

    module_name, factory_name = args.app_factory.split(':')
    factory = getattr(importlib.import_module(module_name), factory_name)
    application = factory()

    server = verktyg_server.argparse.make_server(args, application)
    server.serve_forever()
