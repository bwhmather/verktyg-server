"""
    verktyg_server.ssl
    ~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import os
import sys
import ssl
from datetime import datetime, timedelta


def generate_adhoc_ssl_pair(cn=None):
    from random import random
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.backends import default_backend

    # pretty damn sure that this is not actually accepted by anyone
    if cn is None:
        cn = '*'

    now = datetime.now()

    pkey = rsa.generate_private_key(65537, 2048, backend=default_backend())

    bldr = x509.CertificateBuilder()\
        .serial_number(int(random() * sys.maxsize))\
        .not_valid_before(now)\
        .not_valid_after(datetime.now() + timedelta(days=1))\
        .subject_name(x509.Name([
            x509.NameAttribute(
                x509.NameOID.COMMON_NAME, cn,
            ),
        ]))\
        .issuer_name(x509.Name([
            x509.NameAttribute(
                x509.NameOID.COMMON_NAME, 'Untrusted Authority'
            ),
            x509.NameAttribute(
                x509.NameOID.ORGANIZATION_NAME, 'Self-Signed'
            )
        ]))\
        .public_key(pkey.public_key())

    cert = bldr.sign(pkey, SHA256(), backend=default_backend())

    return cert, pkey


def make_ssl_devcert(base_path, host=None, cn=None):
    """Creates an SSL key for development.  This should be used instead of
    the ``'adhoc'`` key which generates a new cert on each server start.
    It accepts a path for where it should store the key and cert and
    either a host or CN.  If a host is given it will use the CN
    ``*.host/CN=host``.

    For more information see :func:`run_simple`.

    :param base_path:
        The path to the certificate and key.  The extension ``.crt`` is added
        for the certificate, ``.key`` is added for the key.
    :param host:
        The name of the host.  This can be used as an alternative for the
        `cn`.
    :param cn:
        The `CN` to use.
    """
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PrivateFormat, NoEncryption
    )

    if host is not None:
        cn = '*.%s/CN=%s' % (host, host)
    cert, pkey = generate_adhoc_ssl_pair(cn=cn)

    cert_file = base_path + '.crt'
    pkey_file = base_path + '.key'

    with open(cert_file, 'wb') as f:
        f.write(cert.public_bytes(Encoding.PEM))
    with open(pkey_file, 'wb') as f:
        f.write(pkey.private_bytes(
            Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
        ))

    return cert_file, pkey_file


def make_adhoc_ssl_context():
    """Generates an adhoc SSL context for the development server."""
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PrivateFormat, NoEncryption
    )
    import tempfile
    import atexit

    cert, pkey = generate_adhoc_ssl_pair()
    cert_handle, cert_file = tempfile.mkstemp()
    pkey_handle, pkey_file = tempfile.mkstemp()
    atexit.register(os.remove, pkey_file)
    atexit.register(os.remove, cert_file)

    os.write(cert_handle, cert.public_bytes(Encoding.PEM))
    os.write(pkey_handle, pkey.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    ))
    os.close(cert_handle)
    os.close(pkey_handle)
    ctx = load_ssl_context(cert_file, pkey_file)
    return ctx


def load_ssl_context(cert_file, pkey_file=None):
    """Creates an SSL context from a certificate and private key file.

    :param cert_file:
        Path of the certificate to use.
    :param pkey_file:
        Path of the private key to use. If not given, the key will be obtained
        from the certificate file.
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_file, pkey_file)

    return context
