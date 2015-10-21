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
import verktyg_server.ssl


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


def add_arguments(parser):
    """Takes an ``argparse`` parser and populates it with the arguments
    required by :func:`make_server`
    """
    group = parser.add_argument_group("Serving Options")
    addr_group = group.add_mutually_exclusive_group(required=True)
    addr_group.add_argument(
        '--socket', type=str,
        help=(
            'Path of a unix socket to listen on.  If the socket does '
            'not exist it will be created'
        )
    )
    addr_group.add_argument(
        '--address', type=_AddressType(),
        help=(
            'Hostname or address to listen on.  Can include optional port'
        )
    )
    addr_group.add_argument(
        '--fd', type=str,
        help=(
            'File descriptor to listen on'
        )
    )

    group = parser.add_argument_group("SSL Options")
    group.add_argument(
        '--certificate', type=str,
        help=(
            'Path to certificate file'
        )
    )
    group.add_argument(
        '--private-key', type=str,
        help=(
            'Path to private key file'
        )
    )


def make_server(args, application):
    """Takes an `argparse` namespace and a wsgi application and returns a
    new http server
    """
    if args.certificate:
        ssl_context = verktyg_server.ssl.load_ssl_context(
            args.certificate, args.private_key
        )
    else:
        if args.private_key:
            raise ValueError("Private key provided but no certificate")
        ssl_context = None

    if args.socket:
        raise NotImplementedError()

    elif args.address:
        scheme = args.address.scheme
        if not scheme:
            scheme = 'https' if ssl_context else 'http'

        address = args.address.hostname

        if not args.address.port:
            port = {
                'http': 80,
                'https': 443,
            }[scheme]

        if scheme == 'https' and not ssl_context:
            ssl_context = verktyg_server.ssl.make_adhoc_ssl_context()

    elif args.fd:
        scheme = 'fd'
        address = str(int(args.fd))
        port = None

    socket = verktyg_server.make_socket(
        '{scheme}://{address}'.format(scheme=scheme, address=address), port,
        ssl_context=ssl_context
    )

    server = verktyg_server.make_server(socket, application)
    return server
