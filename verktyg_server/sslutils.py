"""
    verktyg_server.ssl
    ~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import contextlib
from uuid import uuid4
from datetime import datetime, timedelta
import os
import tempfile
import ssl


def _serialize_private_key(key):
    from cryptography.hazmat.primitives import serialization

    return key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )


def _deserialize_private_key(key_str):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    return serialization.load_pem_private_key(
        key_str, backend=default_backend(), password=None
    )


def _serialize_certificate(cert):
    from cryptography.hazmat.primitives import serialization

    return cert.public_bytes(
        serialization.Encoding.PEM
    )


def _deserialize_certificate(cert_str):
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    return x509.load_pem_x509_certificate(
        cert_str, backend=default_backend()
    )


def _key_usage_extension(
            *, digital_signature=False, content_commitment=False,
            key_encipherment=False, data_encipherment=False,
            key_agreement=False, key_cert_sign=False, crl_sign=False,
            encipher_only=False, decipher_only=False
        ):
    from cryptography import x509
    return x509.KeyUsage(
        digital_signature=digital_signature,
        content_commitment=content_commitment,
        key_encipherment=key_encipherment,
        data_encipherment=data_encipherment,
        key_agreement=key_agreement,
        key_cert_sign=key_cert_sign, crl_sign=crl_sign,
        encipher_only=encipher_only, decipher_only=decipher_only
    )


def generate_adhoc_ssl_pair(*, cn=None, host=None):
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.backends import default_backend

    now = datetime.utcnow()
    not_valid_before = now
    not_valid_after = now + timedelta(days=16)

    if cn and host or not (cn or host):
        raise ValueError("Please specify one of common name or host")

    if host is not None:
        cn = '*.{host}/CN={host}'.format(host=host)

    name = x509.Name([
        x509.NameAttribute(
            x509.NameOID.COMMON_NAME, cn,
        ),
    ])

    key = rsa.generate_private_key(65537, 2048, backend=default_backend())

    bldr = x509.CertificateBuilder()\
        .serial_number(uuid4().int)\
        .subject_name(name)\
        .issuer_name(name)\
        .not_valid_before(not_valid_before)\
        .not_valid_after(not_valid_after)\
        .add_extension(
            _key_usage_extension(key_agreement=True), critical=True
        )\
        .public_key(key.public_key())

    cert = bldr.sign(key, SHA256(), backend=default_backend())

    return _serialize_certificate(cert), _serialize_private_key(key)


def make_adhoc_ssl_context():
    """Generates an adhoc SSL context for the development server."""
    cert, key = generate_adhoc_ssl_pair(host='example.com')

    with contextlib.ExitStack() as clean_stack:
        with contextlib.ExitStack() as close_stack:
            cert_handle, cert_file = tempfile.mkstemp(
                prefix='verktyg-adhoc-', suffix='.cert.pem'
            )
            close_stack.callback(os.close, cert_handle)
            clean_stack.callback(os.remove, cert_file)

            key_handle, key_file = tempfile.mkstemp(
                prefix='verktyg-adhoc-', suffix='.key.pem'
            )
            close_stack.callback(os.close, key_handle)
            clean_stack.callback(os.remove, key_file)

            os.write(cert_handle, cert)
            os.write(key_handle, key)

        return load_ssl_context(cert_file, key_file)


def load_ssl_context(cert_file, key_file=None):
    """Creates an SSL context from a certificate and private key file.

    :param cert_file:
        Path of the certificate to use.
    :param key_file:
        Path of the private key to use. If not given, the key will be obtained
        from the certificate file.
    """
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(cert_file, key_file)

    return context
