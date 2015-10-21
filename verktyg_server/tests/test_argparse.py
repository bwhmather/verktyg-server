"""
    verktyg_server.tests.test_argparse
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import unittest
import argparse

from http.client import HTTPConnection
from threading import Thread

from verktyg_server.argparse import add_arguments, make_server

import logging
logging.disable(logging.CRITICAL)


class ParseError(Exception):
    pass


class SilentArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ParseError(message)


class ArgParseTestCase(unittest.TestCase):
    def test_socket(self):
        parser = SilentArgumentParser()

        add_arguments(parser)

        options = parser.parse_args('--socket /path/to/socket'.split())

        self.assertEqual(options.socket, '/path/to/socket')
        self.assertIsNone(options.address)
        self.assertIsNone(options.fd)
        self.assertIsNone(options.certificate)
        self.assertIsNone(options.private_key)

    def test_mutual_exclusion(self):
        parser = SilentArgumentParser()
        add_arguments(parser)

        with self.assertRaises(ParseError):
            options = parser.parse_args(
                '--socket socket --address address'.split()
            )
