#!/usr/bin/env python3

import unittest
from cupp3 import *


class TestCupp3(unittest.TestCase):
    def setUp(self):
        read_config()

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


if __name__ == '__main__':
    unittest.main()
