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
        pass

if __name__ == '__main__':
    unittest.main()
