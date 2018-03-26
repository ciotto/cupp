#!/usr/bin/env python3
import types
import unittest
import input_mocker
import cupp3
from cupp3 import *


class CuppMocker:
    def __init__(self, reset=False):
        self.reset = reset

    def __enter__(self):
        # Save values
        self.config = cupp3.CONFIG
        self.ftp_config = cupp3.FTP_CONFIG
        self.leet_config = cupp3.LEET_CONFIG
        self.verbose = cupp3.verbose

        if self.reset:
            # Reset values
            cupp3.CONFIG = {}
            cupp3.FTP_CONFIG = {}
            cupp3.LEET_CONFIG = {}

    def __exit__(self, *exc_info):
        # Reset values
        cupp3.CONFIG = self.config
        cupp3.FTP_CONFIG = self.ftp_config
        cupp3.LEET_CONFIG = self.leet_config
        cupp3.verbose = self.verbose


class TestCupp3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read_config()

    def setUp(self):
        self.mocker = CuppMocker()
        self.mocker.__enter__()

    def tearDown(self):
        self.mocker.__exit__()

    @input_mocker.patch()
    def test_input(self):
        self.assertEqual(input_text(), 'y')

    def test_cupp_mocker(self):
        self.assertNotEqual(cupp3.CONFIG, {})
        self.assertNotEqual(cupp3.FTP_CONFIG, {})
        self.assertNotEqual(cupp3.LEET_CONFIG, {})
        self.assertEqual(cupp3.verbose, False)

        with CuppMocker(True):
            self.assertEqual(cupp3.CONFIG, {})
            self.assertEqual(cupp3.FTP_CONFIG, {})
            self.assertEqual(cupp3.LEET_CONFIG, {})
            self.assertEqual(cupp3.verbose, False)

            cupp3.CONFIG = {'foo': 'bar'}
            cupp3.FTP_CONFIG = {'foo': 'bar'}
            cupp3.LEET_CONFIG = {'foo': 'bar'}
            cupp3.verbose = True

            self.assertEqual(cupp3.CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.FTP_CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.LEET_CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.verbose, True)
        self.assertNotEqual(cupp3.CONFIG, {})
        self.assertNotEqual(cupp3.FTP_CONFIG, {})
        self.assertNotEqual(cupp3.LEET_CONFIG, {})
        self.assertEqual(cupp3.verbose, False)

    def test_ftp_download(self):
        if not os.path.isdir('dictionaries'):
            os.mkdir('dictionaries')

        download_ftp_files('french', 'dico.gz')

        self.assertTrue(os.path.isfile(os.path.join('dictionaries', 'french', 'dico.gz')))

    def test_parser(self):
        parser = get_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])

        with self.assertRaises(SystemExit):
            parser.parse_args(['-i', '-v'])

        with self.assertRaises(SystemExit):
            parser.parse_args(['-i', '-a'])

        with self.assertRaises(SystemExit):
            parser.parse_args(['-i', '-l'])

        args = parser.parse_args(['-a'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-a', '--quiet'])
        self.assertTrue(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-l'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-l', '-q'])
        self.assertFalse(args.alecto)
        self.assertTrue(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-a'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-w', 'dictionary.txt', '--quiet'])
        self.assertFalse(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertTrue(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-i'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['--interactive', '-q'])
        self.assertFalse(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertTrue(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['--version'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-v', '--quiet'])
        self.assertFalse(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertTrue(args.version)

    def test_concats(self):
        result = concats(['foo', 'bar'], 0, 2)
        self.assertEqual(type(result), types.GeneratorType)
        self.assertEqual(
            list(result),
            ['foo0', 'foo1', 'bar0', 'bar1', ]
        )

    def test_komb(self):
        result = komb(['foo', 'bar'], ['qwe', 'asd'])
        self.assertEqual(type(result), types.GeneratorType)
        self.assertEqual(
            list(result),
            ['fooqwe', 'fooasd', 'barqwe', 'barasd', ]
        )

    def test_leet_replace(self):
        result = leet_replace('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                              'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

        self.assertEqual(
            result,
            '4bcd3f9h1jklmn0pqr57uvwxy2ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            '4bcd3f9h1jklmn0pqr57uvwxy2ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )

    def test_output_utilities(self):
        self.assertEqual(colorize('Message', 32), '\033[1;32mMessage\033[1;m')

        self.assertEqual(info('Message\nmessage'), '\033[1;33m[i]\033[1;m Message\n    message')
        with CuppMocker():
            cupp3.verbose = True
            self.assertEqual(debug('Message\nmessage'), '\033[1;33m[v]\033[1;m Message\n    message')
        self.assertIsNone(debug('Message\nmessage'))
        self.assertEqual(success('Message\nmessage'), '\033[1;32m[+]\033[1;m Message\n    message')
        self.assertEqual(warning('Message\nmessage'), '\033[1;33m[!]\033[1;m Message\n    message')
        self.assertEqual(error('Message\nmessage'), '\033[1;31m[-]\033[1;m Message\n    message')


if __name__ == '__main__':
    unittest.main()
