"""
    verktyg_server.argparse
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import re
from collections import namedtuple
from argparse import ArgumentTypeError

import verktyg_server
import verktyg_server.sslutils


_address_re = re.compile(r'''
    ^
    (?:
        (?P<scheme> [a-z]+)
        ://
    )?
    (?P<hostname>
        (?:
            [A-Za-z0-9]
            [A-Za-z0-9\-]*
        )
        (?:
            \.
            [A-Za-z0-9]
            [A-Za-z0-9\-]*
        )*
    )
    (?:
        :
        (?P<port> [0-9]+)
    )?
    $
''', re.VERBOSE)


_Address = namedtuple('Address', ['scheme', 'hostname', 'port'])


class _AddressType(object):
    def __call__(self, string):
        match = _address_re.match(string)

        if match is None:
            raise ArgumentTypeError("Invalid address %r" % string)

        scheme, hostname, port = match.group('scheme', 'hostname', 'port')

        # TODO should scheme be validated here?
        if scheme and scheme not in {'https', 'http'}:
            raise ArgumentTypeError("Invalid scheme %r" % scheme)

        if port is not None:
            port = int(port)

        return _Address(scheme, hostname, port)


def add_ssl_arguments(parser):
    """Takes an ``argparse`` parser and populates it with the arguments
    required by :func:`make_ssl_context`
    """
    group = parser.add_argument_group("SSL Options")
    group.add_argument(
        '--certificate', type=str,
        help=(
            "Path to certificate file"
        )
    )
    group.add_argument(
        '--private-key', type=str,
        help=(
            "Path to private key file"
        )
    )
    group.add_argument(
        '--adhoc-ssl', type=bool, default=False,
        help=(
            "Create an ssl context with a new self-signed certificate"
        )
    )


def add_socket_arguments(parser):
    """Takes an ``argparse`` parser and populates it with the arguments
    required by :func:`make_socket`
    """
    group = parser.add_argument_group("Serving Options")
    addr_group = group.add_mutually_exclusive_group(required=True)
    addr_group.add_argument(
        '--socket', type=str,
        help=(
            "Path of a unix socket to listen on.  If the socket does "
            "not exist it will be created"
        )
    )
    addr_group.add_argument(
        '--address', type=_AddressType(),
        help=(
            "Hostname or address to listen on.  Can include optional port"
        )
    )
    addr_group.add_argument(
        '--fd', type=str,
        help=(
            "File descriptor to listen on"
        )
    )


def add_arguments(parser):
    """Takes an ``argparse`` parser and populates it with the arguments
    required by :func:`make_server`
    """
    add_socket_arguments(parser)
    add_ssl_arguments(parser)


def make_ssl_context(args):
    """Create a new ssl context with settings from the command line

    :param args:
        An :module:`argparse` namespace populated with the arguments from
        :func:`add_ssl_arguments`

    :returns:
        An :class:`ssl.SSLContext` instance with settings loaded from
        arguments, or``None`` if no ssl context is requested.
    """
    if args.adhoc_ssl:
        if args.certificate or args.private_key:
            raise ValueError(
                "adhoc ssl context requested with details for explicit context"
            )
        ssl_context = verktyg_server.sslutils.make_adhoc_ssl_context()
        return ssl_context

    if args.certificate:
        ssl_context = verktyg_server.sslutils.load_ssl_context(
            args.certificate, args.private_key
        )
        return ssl_context

    if args.private_key:
        raise ValueError("Private key provided but no certificate")

    return None


def make_socket(args, ssl_context=None):
    """Create a new socket using settings from command line

    :param args:
        An :module:`argparse` namespace populated with the arguments from
        :func:`add_socket_arguments`
    :param ssl_context:
        An :class:`ssl.SSLContext` instance or ``None.

    :returns:
        A new stream :class:`socket.Socket` instance.
    """
    if args.socket is not None:
        socket = verktyg_server.make_unix_socket(
            args.socket, ssl_context=ssl_context
        )

    elif args.address is not None:
        scheme = args.address.scheme
        if scheme == 'https' and not ssl_context:
            raise ValueError("ssl server requested but no details for context")

        if scheme == 'http' and ssl_context:
            raise ValueError("trying to create http server with ssl")

        if not scheme:
            scheme = 'https' if ssl_context else 'http'

        if scheme not in {'https', 'http'}:
            raise ValueError(
                "if provided scheme should be either http or https"
            )

        address = args.address.hostname

        port = args.address.port
        if not port:
            port = {
                'http': 80,
                'https': 443,
            }[scheme]

        socket = verktyg_server.make_inet_socket(
            address, port, ssl_context=ssl_context
        )

    elif args.fd is not None:
        socket = verktyg_server.make_fd_socket(args.fd)

    return socket


def make_server(args, application):
    """Create a new http server using settings from the command line

    :param args:
        An :module:`argparse` namespace populated with the arguments from
        :func:`add_arguments`
    :param application:
        The wsgi application to serve
    :returns:
        A verktyg server that can be run by calling the `run_forever` method
    """
    ssl_context = make_ssl_context(args)

    socket = make_socket(args, ssl_context)

    server = verktyg_server.make_server(socket, application)
    return server
