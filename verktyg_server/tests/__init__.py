"""
    verktyg_server.tests
    ~~~~~~~~~~~~~~~~~~~~

    :copyright:
        (c) 2015 by Ben Mather.
    :license:
        BSD, see LICENSE for more details.
"""
import unittest

from verktyg_server.tests import (
    test_ssl, test_sockets, test_serving, test_testing, test_argparse,
)


loader = unittest.TestLoader()
suite = unittest.TestSuite((
    loader.loadTestsFromModule(test_ssl),
    loader.loadTestsFromModule(test_sockets),
    loader.loadTestsFromModule(test_serving),
    loader.loadTestsFromModule(test_testing),
    loader.loadTestsFromModule(test_argparse),
))
