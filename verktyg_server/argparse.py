"""
    verktyg_server.argparse
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import verktyg_server
import urllib.parse


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
        '--address', type=str,
        help=(
            'Hostname or address to listen on.  Can include optional port'
        )
    )
    addr_group.add_argument(
        '--fd', type=str,
        help=(
            'file descriptor to listen on'
        )
    )


def make_server(args, application):
    """Takes an `argparse` namespace and a wsgi application and returns a
    new http server
    """
    if args.socket:
        raise NotImplementedError()
    elif args.address:
        components = urllib.parse.urlparse(args.address)
        if components.scheme == 'https':
            raise NotImplementedError()
        if components.params or components.query or components.fragment:
            raise ValueError("expected host name and optionally port")
        socket = verktyg_server.make_socket(
            components.host, components.port
        )
    elif args.fd:
        socket = verktyg_server.make_socket('fd://%s' % args.fd)

    server = verktyg_server.make_server(socket, application)
    return server
