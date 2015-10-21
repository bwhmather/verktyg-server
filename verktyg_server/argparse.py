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
        ssl_context = load_ssl_context(args.certificate, args.private_key)
    else:
        if args.private_key:
            raise ValueError("Private key provided but no certificate")
        ssl_context = None

    if args.socket:
        raise NotImplementedError()

    elif args.address:
        components = urllib.parse.urlparse(args.address)

        if any(components[2:]):
            raise ValueError("Expected plain address")

        if components.scheme and components.scheme not in {'https', 'http'}:
            raise ValueError()

        scheme = components.scheme
        if not scheme:
            scheme = 'https' if ssl_context else 'http'

        address = components.hostname

        if not components.port:
            port = {
                'http': 80,
                'https': 443,
            }[scheme]

        if scheme == 'https' and not ssl_context:
            ssl_context = make_adhoc_ssl_context()

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
