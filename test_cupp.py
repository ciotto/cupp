#!/usr/bin/env python3
import tempfile
import types
import unittest
from mock import patch
import input_mocker
from shutil import copyfile
import cupp3
from cupp3 import *


class CuppMocker:
    def __init__(self, reset=False):
        self.reset = reset

    def __enter__(self):
        # Save values
        self.config = dict(cupp3.CONFIG)
        self.ftp_config = dict(cupp3.FTP_CONFIG)
        self.leet_config = dict(cupp3.LEET_CONFIG)
        self.verbose = cupp3.verbose
        self.cupp_dir = cupp3.cupp_dir

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
        cupp3.cupp_dir = self.cupp_dir


class TestCupp3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read_config()

    def setUp(self):
        self.mocker = CuppMocker()
        self.mocker.__enter__()

    def tearDown(self):
        self.mocker.__exit__()

    def assertFileEqual(self, path1, path2):
        with open(path1, 'r') as f1:
            with open(path2, 'r') as f2:
                self.assertEqual(f1.read(), f2.read())

    @input_mocker.patch(['y', 'd', 'n'])
    def test_input(self):
        self.assertEqual(input_text(), 'y')
        self.assertEqual(input_text(), 'd')
        self.assertEqual(input_text(), 'n')

        self.assertEqual(input_text(validate='^[yYnN]$'), 'y')
        self.assertEqual(input_text(validate='^[yYnN]$'), 'n')

        self.assertEqual(input_text(validate='[yYnN]'), 'y')
        self.assertEqual(input_text(validate='[yYnN]'), 'n')

        self.assertEqual(input_text(validate='[yYnN]', error_msg='Error'), 'y')
        self.assertEqual(input_text(validate='[yYnN]', error_msg='Error'), 'n')

        def _v(v):
            if v == 'd':
                raise IOError('Message')
            return v
        self.assertEqual(input_text(validate=_v), 'y')
        self.assertEqual(input_text(validate=_v), 'n')

        self.assertEqual(input_text(validate=_v, error_msg='Error'), 'y')
        self.assertEqual(input_text(validate=_v, error_msg='Error'), 'n')

        with input_mocker.InputMocker(['']):
            self.assertEqual(input_text(validate='', default='n'), 'n')

    def test_cupp_mocker(self):
        self.assertNotEqual(cupp3.CONFIG, {})
        self.assertNotEqual(cupp3.FTP_CONFIG, {})
        self.assertNotEqual(cupp3.LEET_CONFIG, {})
        self.assertEqual(cupp3.verbose, False)
        self.assertNotEqual(cupp3.cupp_dir, '/foo')

        with CuppMocker(True):
            self.assertEqual(cupp3.CONFIG, {})
            self.assertEqual(cupp3.FTP_CONFIG, {})
            self.assertEqual(cupp3.LEET_CONFIG, {})
            self.assertEqual(cupp3.verbose, False)
            self.assertNotEqual(cupp3.cupp_dir, '/foo')

            cupp3.CONFIG = {'foo': 'bar'}
            cupp3.FTP_CONFIG = {'foo': 'bar'}
            cupp3.LEET_CONFIG = {'foo': 'bar'}
            cupp3.verbose = True
            cupp3.cupp_dir = '/foo'

            self.assertEqual(cupp3.CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.FTP_CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.LEET_CONFIG, {'foo': 'bar'})
            self.assertEqual(cupp3.verbose, True)
            self.assertEqual(cupp3.cupp_dir, '/foo')
        self.assertNotEqual(cupp3.CONFIG, {})
        self.assertNotEqual(cupp3.FTP_CONFIG, {})
        self.assertNotEqual(cupp3.LEET_CONFIG, {})
        self.assertEqual(cupp3.verbose, False)
        self.assertNotEqual(cupp3.cupp_dir, '/foo')

    def test_read_config(self):
        # Create temp conf file
        tempfile.gettempdir()
        tempfile_path = os.path.join(tempfile.tempdir, 'cupp.cfg')
        cwdfile_path = os.path.join(os.getcwd(), 'cupp.cfg')
        copyfile('cupp.cfg', tempfile_path)

        config = {
            'alectourl': 'http://www.helith.net/projects/alecto/alectodb.csv.gz',
            'chars': ['!', '@', "'#'", '$', '%', '&', '*'],
            'numfrom': 0,
            'numto': 100,
            'threshold': 200,
            'wcfrom': 5,
            'wcto': 12,
            'years': [
                '2008',
                '2009',
                '2010',
                '2011',
                '2012',
                '2013',
                '2014',
                '2015',
                '2016',
                '2017',
                '2018',
            ]
        }
        ftp_config = {
            'name': 'FUNET',
            'password': 'cupp3',
            'path': '/pub/unix/security/passwd/crack/dictionaries/',
            'url': 'ftp.funet.fi',
            'user': 'anonymous',
        }
        leet_config = {
            'a': '4',
            'e': '3',
            'g': '9',
            'i': '1',
            'o': '0',
            's': '5',
            't': '7',
            'z': '2',
        }

        # 1. -> test passing parameter override other paths
        with CuppMocker(True):
            result = read_config(tempfile_path)
            self.assertEqual(result, tempfile_path)

            self.assertEqual(cupp3.CONFIG, config)
            self.assertEqual(cupp3.FTP_CONFIG, ftp_config)
            self.assertEqual(cupp3.LEET_CONFIG, leet_config)

        # 2. -> if not exist use cwd version
        with CuppMocker(True):
            cupp3.cupp_dir = '/foo/bar'

            result = read_config()
            self.assertEqual(result, cwdfile_path)

            self.assertEqual(cupp3.CONFIG, config)
            self.assertEqual(cupp3.FTP_CONFIG, ftp_config)
            self.assertEqual(cupp3.LEET_CONFIG, leet_config)

        # 3. -> if exist together use cwd version
        with CuppMocker(True):
            cupp3.cupp_dir = tempfile.tempdir

            result = read_config()
            self.assertEqual(result, cwdfile_path)

        # 4. -> if not exist cwd version use cupp dir version
        with CuppMocker(True):
            with patch('os.getcwd') as getcwd_mock:
                getcwd_mock.return_value = '/foo/bar'
                cupp3.cupp_dir = tempfile.tempdir

                result = read_config()
                self.assertEqual(result, tempfile_path)

                self.assertEqual(cupp3.CONFIG, config)
                self.assertEqual(cupp3.FTP_CONFIG, ftp_config)
                self.assertEqual(cupp3.LEET_CONFIG, leet_config)

        # 5. -> if CUPP_CFG env variable is set use that
        with CuppMocker(True):
            with patch.dict('os.environ', {'CUPP_CFG': tempfile_path}):
                result = read_config()
                self.assertEqual(result, tempfile_path)

                self.assertEqual(cupp3.CONFIG, config)
                self.assertEqual(cupp3.FTP_CONFIG, ftp_config)
                self.assertEqual(cupp3.LEET_CONFIG, leet_config)

        # 6. -> if CUPP_CFG env variable is set and passing parameter use parameter
        with CuppMocker(True):
            with patch.dict('os.environ', {'CUPP_CFG': cwdfile_path}):
                result = read_config(tempfile_path)
                self.assertEqual(result, tempfile_path)

                self.assertEqual(cupp3.CONFIG, config)
                self.assertEqual(cupp3.FTP_CONFIG, ftp_config)
                self.assertEqual(cupp3.LEET_CONFIG, leet_config)

        # 7. -> config file not found
        with CuppMocker(True):
            with patch('os.getcwd') as getcwd_mock:
                getcwd_mock.return_value = '/foo/bar'
                cupp3.cupp_dir = '/foo/bar'

                with self.assertRaises(SystemExit) as c:
                    read_config()
                self.assertEqual(c.exception.code, 1)

        # 8. -> config file does not exist
        with self.assertRaises(SystemExit) as c:
            read_config('foo/bar.cfg')
        self.assertEqual(c.exception.code, 1)

    def test_ftp_download(self):
        if not os.path.isdir('dictionaries'):
            os.mkdir('dictionaries')

        download_ftp_files('french', 'dico.gz')

        self.assertTrue(os.path.isfile(os.path.join('dictionaries', 'french', 'dico.gz')))

    def test_parser(self):
        parser = get_parser()
        with self.assertRaises(SystemExit) as c:
            parser.parse_args([])
        self.assertEqual(c.exception.code, 2)

        with self.assertRaises(SystemExit) as c:
            parser.parse_args(['-i', '-v'])
        self.assertEqual(c.exception.code, 2)

        with self.assertRaises(SystemExit) as c:
            parser.parse_args(['-i', '-a'])
        self.assertEqual(c.exception.code, 2)

        with self.assertRaises(SystemExit) as c:
            parser.parse_args(['-i', '-l'])
        self.assertEqual(c.exception.code, 2)

        args = parser.parse_args(['-i', '-c', 'foo/bar.cfg'])
        self.assertEqual(args.config, 'foo/bar.cfg')
        args = parser.parse_args(['-l', '--config', 'bar/foo.cfg'])
        self.assertEqual(args.config, 'bar/foo.cfg')
        self.assertFalse(args.alecto)
        self.assertTrue(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertFalse(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-a'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-a', '--quiet'])
        self.assertIsNone(args.config)
        self.assertTrue(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-l'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-l', '-q'])
        self.assertIsNone(args.config)
        self.assertFalse(args.alecto)
        self.assertTrue(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-a'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-w', 'dictionary.txt', '--quiet'])
        self.assertIsNone(args.config)
        self.assertFalse(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertEqual(args.improve, 'dictionary.txt')
        self.assertFalse(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['-i'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['--interactive', '-q'])
        self.assertIsNone(args.config)
        self.assertFalse(args.alecto)
        self.assertFalse(args.download_wordlist)
        self.assertFalse(args.improve)
        self.assertTrue(args.interactive)
        self.assertTrue(args.quiet)
        self.assertFalse(args.version)

        args = parser.parse_args(['--version'])
        self.assertFalse(args.quiet)
        args = parser.parse_args(['-v', '--quiet'])
        self.assertIsNone(args.config)
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

    def test_version(self):
        with self.assertRaises(SystemExit) as c:
            version()
        self.assertIsNone(c.exception.code)

    def test_interactive(self):
        # 1. -> name only
        inputs = ['foo'] + (['']*15)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_01.txt')

        # 2. -> all user data
        inputs = ['foo', 'bar', 'qwe', '12101990'] + (['']*12)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_02.txt')

        # 3. -> user data and partner data
        inputs = ['foo', 'bar', 'qwe', '12101990', 'rty', 'asd', '05121990'] + (['']*9)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_03.txt')

        # 4. -> user data, partner data and child name
        inputs = ['foo', 'bar', 'qwe', '12101990', 'rty', 'asd', '05121990', 'fgh', 'zxc', '23042000'] + (['']*6)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_04.txt')

        # 5. -> all data
        inputs = [
            'foo', 'bar', 'qwe', '12101990', 'rty', 'asd', '05121990', 'fgh', 'zxc', '23042000', 'vbn', 'jkl'
        ] + (['']*4)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_05.txt')

        # 6. -> all data and all options
        inputs = [
            'foo', 'bar', 'qwe', '12101990', 'rty', 'asd', '05121990', 'fgh', 'zxc', '23042000', 'vbn', 'jkl'
        ] + (['y']*5)
        with input_mocker.InputMocker(inputs):
            with self.assertRaises(SystemExit) as c:
                interactive()
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('foo.txt', 'tests/interactive_06.txt')

    def test_improve_dictionary(self):
        # 1. -> invalid file
        with input_mocker.InputMocker(['']):
            with self.assertRaises(SystemExit) as c:
                improve_dictionary('tests/fake.txt')
            self.assertEqual(c.exception.code, 1)

        # 2. -> invalid file
        with CuppMocker():
            cupp3.CONFIG['threshold'] = True
            with input_mocker.InputMocker(['y']):
                with self.assertRaises(SystemExit) as c:
                    improve_dictionary('tests/improve.txt')
                self.assertEqual(c.exception.code, 1)

        # 3. -> all options default
        with input_mocker.InputMocker(['']):
            with self.assertRaises(SystemExit) as c:
                improve_dictionary('tests/improve.txt')
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('tests/improve.txt.cupp.txt', 'tests/improve_01.txt')

        # 4. -> all options yes
        with input_mocker.InputMocker(['y']):
            with self.assertRaises(SystemExit) as c:
                improve_dictionary('tests/improve.txt')
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('tests/improve.txt.cupp.txt', 'tests/improve_02.txt')

        # 5. -> all options yes
        with input_mocker.InputMocker(['n', 'y', 'y', 'y']):
            with self.assertRaises(SystemExit) as c:
                improve_dictionary('tests/improve.txt')
            self.assertIsNone(c.exception.code)

            self.assertFileEqual('tests/improve.txt.cupp.txt', 'tests/improve_03.txt')

    @input_mocker.patch(['0', '-1', '39', '1', '37', '38'])
    def test_download_wordlist(self):
        def _mock(*a):
            def _download_ftp_files(*args):
                self.assertEqual(args, a)
            return _download_ftp_files

        with patch('cupp3.download_ftp_files', _mock(
                'Moby', 'mhyph.tar.gz', 'mlang.tar.gz', 'moby.tar.gz',
                'mpos.tar.gz', 'mpron.tar.gz', 'mthes.tar.gz', 'mwords.tar.gz')):
            download_wordlist()

        with patch('cupp3.download_ftp_files', _mock('yiddish', 'yiddish.gz')):
            download_wordlist()

        with self.assertRaises(SystemExit) as c:
            download_wordlist()
        self.assertIsNone(c.exception.code)


if __name__ == '__main__':
    unittest.main()
