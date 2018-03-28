#!/usr/bin/env python3
#
#  Muris Kurgas aka j0rgan
#  j0rgan [at] remote-exploit [dot] org
#  http://www.remote-exploit.org
#  http://www.azuzi.me
#
#  See 'docs/LICENSE' and 'docs/README' for more information.
"""Common User Passwords Profiler"""

from __future__ import print_function

__author__ = 'Muris Kurgas'
__license__ = 'GPL'
__version__ = '3.1.0-alpha'

import re
import argparse
from configparser import ConfigParser
import csv
import ftplib
import functools
import gzip
import os
import sys
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

try:
    import readline
except ImportError:
    pass

COW_BANNER = """ ___________
 \033[07m  cupp.py! \033[27m                # Common
      \\                     # User
       \\   \033[1;31m,__,\033[1;m             # Passwords
        \\  \033[1;31m(\033[1;moo\033[1;31m)____\033[1;m         # Profiler
           \033[1;31m(__)    )\\ \033[1;m
           \033[1;31m   ||--|| \033[1;m\033[05m*\033[25m\033[1;m   Muris Kurgas <j0rgan@remote-exploit.org>

"""
CONFIG = {}
FTP_CONFIG = {}
LEET_CONFIG = {}

verbose = False
cupp_dir = os.path.dirname(os.path.realpath(__file__))


def main():
    """Command-line interface to the cupp utility"""

    args = get_parser().parse_args()

    global verbose
    verbose = args.verbose

    if not args.quiet:
        print(COW_BANNER)

    read_config(args.config)

    if args.version:
        version()
    elif args.interactive:
        interactive()
    elif args.download_wordlist:
        download_wordlist()
    elif args.alecto:
        alectodb_download()
    elif args.improve:
        improve_dictionary(args.improve)


def colorize(msg, color):
    return u'\033[1;%sm%s\033[1;m' % (color, msg)


def info(msg, symbol='[i]', color=33, file=None):
    a = msg.splitlines()
    a[0] = u'%s %s' % (colorize(symbol, color), a[0])

    result = u'\n    '.join(a)
    print(result, file=file)
    return result


def debug(msg):
    if verbose:
        return info(msg, '[v]')
    return None


def success(msg):
    return info(msg, '[+]', 32)


def warning(msg):
    return info(msg, '[!]', 33)


def error(msg):
    return info(msg, '[-]', 31, sys.stderr)


def final_message(file_path, dictionary):
    info("Saving dictionary to %s counting %s words." % (colorize(file_path, 31), colorize(len(dictionary), 31)))
    success("Now load your pistolero with %s and shoot! Good luck!" % colorize(file_path, 31))
    sys.exit()


def input_text(msg=None, default=None, validate=None, error_msg=None):
    def _i():
        if sys.version_info.major >= 3:
            return input(msg)
        return raw_input(msg)

    # This code is based on fabric.operations.prompt
    value = None
    while value is None:
        # Get input
        value = _i()
        # Handle validation
        if validate:
            # Callable
            if callable(validate):
                # Callable validate() must raise an exception if validation
                # fails.
                try:
                    value = validate(value)
                except Exception as e:
                    # Reset value so we stay in the loop
                    value = None
                    if error_msg:
                        error(error_msg)
                    else:
                        error('Invalid input:\n%s' % e.message)
            # String / regex must match and will be empty if validation fails.
            else:
                # Need to transform regex into full-matching one if it's not.
                if not validate.startswith('^'):
                    validate = r'^' + validate
                if not validate.endswith('$'):
                    validate += r'$'
                result = re.findall(validate, value)
                if not result:
                    if error_msg:
                        error(error_msg)
                    else:
                        error("Invalid input:\n'%s' does not match '%s'" % (value, validate))
                    # Reset value so we stay in the loop
                    value = None

    if not value and default:
        return default
    return value


# Separate into a function for testing must enter a name at lurposes
def get_parser():
    """Create and return a parser (argparse.ArgumentParser instance) for main()
    to use"""
    parser = argparse.ArgumentParser(description='Common User Passwords Profiler')
    parser.add_argument('-V', '--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('-c', '--config', metavar='FILENAME',
                       help='Use this option to use specific config file', default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--interactive', action='store_true',
                       help='Interactive questions for user password profiling')
    group.add_argument('-w', dest='improve', metavar='FILENAME',
                       help='Use this option to improve existing dictionary,'
                       ' or WyD.pl output to make some pwnsauce')
    group.add_argument('-l', dest='download_wordlist', action='store_true',
                       help='Download huge wordlists from repository')
    group.add_argument('-a', dest='alecto', action='store_true',
                       help='Parse default usernames and passwords directly'
                       ' from Alecto DB. Project Alecto uses purified'
                       ' databases of Phenoelit and CIRT which were merged'
                       ' and enhanced')
    group.add_argument('-v', '--version', action='store_true',
                       help='version of this program')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Quiet mode (don't print banner)")

    return parser


def version():
    """Display version and exit."""
    print("\n \033[1;31m[ cupp.py ]  v3.1.0-alpha\033[1;m\n")
    print(" * Hacked up by j0rgan - j0rgan@remote-exploit.org")
    print(" * http://www.remote-exploit.org\n")
    print(" Take a look ./README.md file for more info about the program\n")
    sys.exit()


def read_config(file_path=None):
    """Read the given configuration file and update global variables to reflect
    changes (CONFIG, FTP_CONFIG, LEET_CONFIG)."""
    #global CONFIG, FTP_CONFIG, LEET_CONFIG

    config_files = [
        os.path.join(os.getcwd(), 'cupp.cfg'),
        os.path.join(cupp_dir, 'cupp.cfg'),
    ]

    if not file_path:
        if 'CUPP_CFG' in os.environ:
            file_path = os.environ['CUPP_CFG']
        else:
            for f in config_files:
                if os.path.isfile(f):
                    file_path = f
                    break
                debug('Config file %s does not exist' % f)

            if not file_path:
                error('Config file not found')
                exit(1)

    if not os.path.isfile(file_path):
        error('Config file %s does not exist' % file_path)
        exit(1)
    debug('use %s config file' % file_path)

    # Reading configuration file
    config = ConfigParser()
    config.read(file_path)

    CONFIG.update({
        'years':     config.get('years', 'years').split(','),
        'chars':     config.get('specialchars', 'chars').split(','),

        'numfrom':   config.getint('nums', 'from'),
        'numto':     config.getint('nums', 'to'),

        'wcfrom':    config.getint('nums', 'wcfrom'),
        'wcto':      config.getint('nums', 'wcto'),

        'threshold': config.getint('nums', 'threshold'),
        'alectourl': config.get('alecto', 'alectourl')
    })

    # 1337 mode configs, well you can add more lines if you add it to the
    # config file too.
    leet = functools.partial(config.get, 'leet')
    LEET_CONFIG.update(dict(a=leet('a'), e=leet('e'), g=leet('g'), i=leet('i'),
                            o=leet('o'), s=leet('s'), t=leet('t'), z=leet('z')))

    ftp_config = functools.partial(config.get, 'downloader')
    FTP_CONFIG.update(dict(name=ftp_config('ftpname'),
                           url=ftp_config('ftpurl'),
                           path=ftp_config('ftppath'),
                           user=ftp_config('ftpuser'),
                           password=ftp_config('ftppass')))

    return file_path


def interactive():
    """Implementation of the -i switch. Interactively question the user and
    create a password dictionary file based on the answer."""
    info("Insert the information about the victim to make a dictionary")
    info("If you don't know all the info, just hit enter when asked! ;)\n")

    # We need some information first!

    name = input_text(
        'First Name: ',
        error_msg='You must enter a name at least!',
        validate='^.+$'
    ).lower().strip()

    surname = input_text("Surname: ").lower().strip()
    nick = input_text("Nickname: ").lower().strip()
    birthdate = input_text(
        "Birthdate (DDMMYYYY): ",
        error_msg='You must enter 8 digits for birthday!',
        validate='^$|^[0-3][0-9][0-1][0-9][0-9]{4}$'
    ).strip()

    print("\n")

    wife = input_text("Partner's name: ").lower().strip()
    wifen = input_text("Partner's nickname: ").lower().strip()
    wifeb = input_text(
        "Partner's birthdate (DDMMYYYY): ",
        error_msg='You must enter 8 digits for birthday!',
        validate='^$|^[0-3][0-9][0-1][0-9][0-9]{4}$'
    ).strip()

    print("\n")

    kid = input_text("Child's name: ").lower().strip()
    kidn = input_text("Child's nickname: ").lower().strip()
    kidb = input_text(
        "Child's birthdate (DDMMYYYY): ",
        error_msg='You must enter 8 digits for birthday!',
        validate='^$|^[0-3][0-9][0-1][0-9][0-9]{4}$'
    ).strip()

    print("\n")

    pet = input_text("Pet's name: ").lower().strip()
    company = input_text("Company name: ").lower().strip()

    print("\n")

    words1 = input_text(
        "Do you want to add some key words about the victim? Y/[N]: ",
        validate='^$|^[yYnN]$'
    ).lower().strip()
    words = []
    if words1 == 'y':
        words = input_text(
            "Please enter the words, comma-separated. [i.e. hacker,juice,black], spaces will be removed: ",
            validate='^[\w \w,]+$'
        ).replace(' ', '').split(',')
        words = list(filter(None, set(words)))

    spechars = []
    prompt = "Do you want to add special characters at the end of words? Y/[N]: "
    spechars1 = input_text(prompt).lower()
    if spechars1 == "y":
        for spec1 in CONFIG['chars']:
            spechars.append(spec1)
            for spec2 in CONFIG['chars']:
                spechars.append(spec1+spec2)
                for spec3 in CONFIG['chars']:
                    spechars.append(spec1+spec2+spec3)

    randnum = input_text("Do you want to add some random numbers at the end of words? Y/[N]: ").lower()
    leetmode = input_text("Leet mode? (i.e. leet = 1337) Y/[N]: ").lower().strip()

    info("Now making a dictionary...")

    # Now me must do some string modifications

    # Birthdays first

    birthdate_yy, birthdate_yyy = birthdate[-2:], birthdate[-3:]
    birthdate_yyyy = birthdate[-4:]
    birthdate_xd, birthdate_xm = birthdate[1:2], birthdate[3:4]
    birthdate_dd, birthdate_mm = birthdate[:2], birthdate[2:4]

    wifeb_yy = wifeb[-2:]
    wifeb_yyy = wifeb[-3:]
    wifeb_yyyy = wifeb[-4:]
    wifeb_xd = wifeb[1:2]
    wifeb_xm = wifeb[3:4]
    wifeb_dd = wifeb[:2]
    wifeb_mm = wifeb[2:4]

    kidb_yy = kidb[-2:]
    kidb_yyy = kidb[-3:]
    kidb_yyyy = kidb[-4:]
    kidb_xd = kidb[1:2]
    kidb_xm = kidb[3:4]
    kidb_dd = kidb[:2]
    kidb_mm = kidb[2:4]


    # Convert first letters to uppercase...
    nameup = name.title()
    surnameup = surname.title()
    nickup = nick.title()
    wifeup = wife.title()
    wifenup = wifen.title()
    kidup = kid.title()
    kidnup = kidn.title()
    petup = pet.title()
    companyup = company.title()
    wordsup = [words1.title() for words1 in words]
    word = words+wordsup

    # reverse a name

    rev_name = name[::-1]
    rev_nameup = nameup[::-1]
    rev_nick = nick[::-1]
    rev_nickup = nickup[::-1]
    rev_wife = wife[::-1]
    rev_wifeup = wifeup[::-1]
    rev_kid = kid[::-1]
    rev_kidup = kidup[::-1]

    reverse = [rev_name, rev_nameup, rev_nick, rev_nickup, rev_wife,
               rev_wifeup, rev_kid, rev_kidup]
    rev_n = [rev_name, rev_nameup, rev_nick, rev_nickup]
    rev_w = [rev_wife, rev_wifeup]
    rev_k = [rev_kid, rev_kidup]
    # Let's do some serious work! This will be a mess of code, but who cares? :)

    # Birthdays combinations
    bds = [birthdate_yy, birthdate_yyy, birthdate_yyyy, birthdate_xd,
           birthdate_xm, birthdate_dd, birthdate_mm]
    bdss = []

    for bds1 in bds:
        bdss.append(bds1)
        for bds2 in bds:
            if bds.index(bds1) != bds.index(bds2):
                bdss.append(bds1 + bds2)
                for bds3 in bds:
                    condition = (bds.index(bds1) != bds.index(bds2) and
                                 bds.index(bds2) != bds.index(bds3) and
                                 bds.index(bds1) != bds.index(bds3))
                    if condition:
                        bdss.append(bds1+bds2+bds3)


    # For a woman...
    wbds = [wifeb_yy, wifeb_yyy, wifeb_yyyy, wifeb_xd, wifeb_xm, wifeb_dd, wifeb_mm]
    wbdss = []

    for wbds1 in wbds:
        wbdss.append(wbds1)
        for wbds2 in wbds:
            if wbds.index(wbds1) != wbds.index(wbds2):
                wbdss.append(wbds1+wbds2)
                for wbds3 in wbds:
                    condition = (wbds.index(wbds1) != wbds.index(wbds2) and
                                 wbds.index(wbds2) != wbds.index(wbds3) and
                                 wbds.index(wbds1) != wbds.index(wbds3))
                    if condition:
                        wbdss.append(wbds1+wbds2+wbds3)


    # and a child...
    kbds = [kidb_yy, kidb_yyy, kidb_yyyy, kidb_xd, kidb_xm, kidb_dd, kidb_mm]
    kbdss = []

    for kbds1 in kbds:
        kbdss.append(kbds1)
        for kbds2 in kbds:
            if kbds.index(kbds1) != kbds.index(kbds2):
                kbdss.append(kbds1+kbds2)
                for kbds3 in kbds:
                    condition = (kbds.index(kbds1) != kbds.index(kbds2) and
                                 kbds.index(kbds2) != kbds.index(kbds3) and
                                 kbds.index(kbds1) != kbds.index(kbds3))
                    if condition:
                        kbdss.append(kbds1+kbds2+kbds3)

    # string combinations
    kombinaac = [pet, petup, company, companyup]
    kombina = [name, surname, nick, nameup, surnameup, nickup]
    kombinaw = [wife, wifen, wifeup, wifenup, surname, surnameup]
    kombinak = [kid, kidn, kidup, kidnup, surname, surnameup]

    kombinaa = []
    for kombina1 in kombina:
        kombinaa.append(kombina1)
        for kombina2 in kombina:
            condition = (kombina.index(kombina1) != kombina.index(kombina2) and
                         kombina.index(kombina1.title()) != kombina.index(kombina2.title()))
            if condition:
                kombinaa.append(kombina1+kombina2)

    kombinaaw = []
    for kombina1 in kombinaw:
        kombinaaw.append(kombina1)
        for kombina2 in kombinaw:
            condition = (kombinaw.index(kombina1) != kombinaw.index(kombina2) and
                         kombinaw.index(kombina1.title()) != kombinaw.index(kombina2.title()))
            if condition:
                kombinaaw.append(kombina1+kombina2)

    kombinaak = []
    for kombina1 in kombinak:
        kombinaak.append(kombina1)
        for kombina2 in kombinak:
            condition = (kombinak.index(kombina1) != kombinak.index(kombina2) and
                         kombinak.index(kombina1.title()) != kombinak.index(kombina2.title()))
            if condition:
                kombinaak.append(kombina1+kombina2)


    komb1 = list(komb(kombinaa, bdss))
    komb2 = list(komb(kombinaaw, wbdss))
    komb3 = list(komb(kombinaak, kbdss))
    komb4 = list(komb(kombinaa, CONFIG['years']))
    komb5 = list(komb(kombinaac, CONFIG['years']))
    komb6 = list(komb(kombinaaw, CONFIG['years']))
    komb7 = list(komb(kombinaak, CONFIG['years']))
    komb8 = list(komb(word, bdss))
    komb9 = list(komb(word, wbdss))
    komb10 = list(komb(word, kbdss))
    komb11 = list(komb(word, CONFIG['years']))
    komb12 = komb13 = komb14 = komb15 = komb16 = komb21 = []
    if randnum == "y":
        komb12 = list(concats(word, CONFIG['numfrom'], CONFIG['numto']))
        komb13 = list(concats(kombinaa, CONFIG['numfrom'], CONFIG['numto']))
        komb14 = list(concats(kombinaac, CONFIG['numfrom'], CONFIG['numto']))
        komb15 = list(concats(kombinaaw, CONFIG['numfrom'], CONFIG['numto']))
        komb16 = list(concats(kombinaak, CONFIG['numfrom'], CONFIG['numto']))
        komb21 = list(concats(reverse, CONFIG['numfrom'], CONFIG['numto']))
    komb17 = list(komb(reverse, CONFIG['years']))
    komb18 = list(komb(rev_w, wbdss))
    komb19 = list(komb(rev_k, kbdss))
    komb20 = list(komb(rev_n, bdss))
    komb001 = komb002 = komb003 = komb004 = komb005 = komb006 = []
    if spechars1 == "y":
        komb001 = list(komb(kombinaa, spechars))
        komb002 = list(komb(kombinaac, spechars))
        komb003 = list(komb(kombinaaw, spechars))
        komb004 = list(komb(kombinaak, spechars))
        komb005 = list(komb(word, spechars))
        komb006 = list(komb(reverse, spechars))

    info("Sorting list and removing duplicates...")

    sets = [set(komb1), set(komb2), set(komb3), set(komb4), set(komb5),
            set(komb6), set(komb7), set(komb8), set(komb9), set(komb10),
            set(komb11), set(komb12), set(komb13), set(komb14), set(komb15),
            set(komb16), set(komb17), set(komb18), set(komb19), set(komb20),
            set(komb21), set(kombinaa), set(kombinaac), set(kombinaaw),
            set(kombinaak), set(word), set(komb001), set(komb002), set(komb003),
            set(komb004), set(komb005), set(komb006)]

    uniqset = set()
    for s in sets:
        uniqset.update(s)

    uniqlist = bdss + wbdss + kbdss + reverse + list(uniqset)

    unique_lista = sorted(set(uniqlist))
    unique_leet = []
    if leetmode == "y":
        for x in unique_lista:
            unique_leet.append(leet_replace(x))

    unique_list = unique_lista + unique_leet

    unique_list_finished = [x for x in unique_list if CONFIG['wcfrom'] < len(x) < CONFIG['wcto']]
    unique_list_finished.sort()

    file_path = '%s.txt' % name
    with open(file_path, 'w') as f:
        f.write(os.linesep.join(unique_list_finished))

    final_message(file_path, unique_list_finished)


def download_ftp_files(ftp_dir, *filenames):
    """Helper function for download_wordlist(). Download the given files from
    the ftp directory."""

    print("\n[+] connecting...\n")
    ftp = ftplib.FTP(FTP_CONFIG['url'], FTP_CONFIG['user'], FTP_CONFIG['password'])
    ftp.cwd(FTP_CONFIG['path'])
    ftp.cwd(ftp_dir)
    dir_prefix = 'dictionaries/%s/' % ftp_dir

    if not os.path.isdir(dir_prefix):
        os.mkdir(dir_prefix)

    def handle_download(target, block):
        "Callback for retrbinary. Prints a progress bar as well."
        target.write(block)
        print('.', end=' ')

    for filename in filenames:
        with open(dir_prefix + filename, 'wb') as outfile:
            print("\n[+] downloading %s..." % filename)
            callback = functools.partial(handle_download, outfile)
            ftp.retrbinary('RETR %s' % filename, callback)
        print(' done.')

    print('[+] file(s) saved to %s' % dir_prefix)
    ftp.quit()


def download_wordlist():
    """Implementation of -l switch. Download wordlists from ftp repository as
    defined in the configuration file."""

    if not os.path.isdir('dictionaries'):
        os.mkdir('dictionaries')

    menu = """
     1   Moby            14      french          27      places
     2   afrikaans       15      german          28      polish
     3   american        16      hindi           29      random
     4   aussie          17      hungarian       30      religion
     5   chinese         18      italian         31      russian
     6   computer        19      japanese        32      science
     7   croatian        20      latin           33      spanish
     8   czech           21      literature      34      swahili
     9   danish          22      movieTV         35      swedish
    10   databases       23      music           36      turkish
    11   dictionaries    24      names           37      yiddish
    12   dutch           25      net             38      exit program
    13   finnish         26      norwegian

    """
    print("\n  Choose the section you want to download:\n")
    print(menu)
    print("\n  Files will be downloaded from %s repository" % FTP_CONFIG['name'])
    print("\n  Tip: After downloading wordlist, you can improve it with -w option\n")

    option = input_text("Enter number: ")
    while not option.isdigit() or int(option) > 38:
        error("Invalid choice.")
        option = input_text("Enter number: ")

    option = int(option)

    if option == 38:
        error('Leaving.')
        sys.exit()

    # integer indexed dict to maintain consistency with the menu shown to the
    # user. plus, easy to inadvertently unorder things up with lists
    arguments = { # the first items of the tuples are the ftp directories.
                  # Do Not Change.
                  1: ('Moby', 'mhyph.tar.gz', 'mlang.tar.gz', 'moby.tar.gz',
                      'mpos.tar.gz', 'mpron.tar.gz', 'mthes.tar.gz', 'mwords.tar.gz'),
                  2: ('afrikaans', 'afr_dbf.zip'),
                  3: ('american', 'dic-0294.tar.gz'),
                  4: ('aussie', 'oz.gz'),
                  5: ('chinese', 'chinese.gz'),
                  6: ('computer', 'Domains.gz', 'Dosref.gz', 'Ftpsites.gz', 'Jargon.gz',
                      'common-passwords.txt.gz', 'etc-hosts.gz', 'foldoc.gz',
                      'language-list.gz', 'unix.gz'),
                  7: ('croatian', 'croatian.gz'),
                  8: ('czech', 'czech-wordlist-ascii-cstug-novak.gz'),
                  9: ('danish', 'danish.words.gz', 'dansk.zip'),
                  10: ('databases', 'acronyms.gz', 'att800.gz',
                       'computer-companies.gz', 'world_heritage.gz'),
                  11: ('dictionaries', 'Antworth.gz', 'CRL.words.gz', 'Roget.words.gz',
                       'Unabr.dict.gz', 'Unix.dict.gz', 'englex-dict.gz',
                       'knuth_britsh.gz', 'knuth_words.gz', 'pocket-dic.gz',
                       'shakesp-glossary.gz', 'special.eng.gz', 'words-english.gz'),
                  12: ('dutch', 'words.dutch.gz'),
                  13: ('finnish', 'finnish.gz', 'firstnames.finnish.gz', 'words.finnish.FAQ.gz'),
                  14: ('french', 'dico.gz'),
                  15: ('german', 'deutsch.dic.gz', 'germanl.gz', 'words.german.gz'),
                  16: ('hindi', 'hindu-names.gz'),
                  17: ('hungarian', 'hungarian.gz'),
                  18: ('italian', 'words.italian.gz'),
                  19: ('japanese', 'words.japanese.gz'),
                  20: ('latin', 'wordlist.aug.gz'),
                  21: ('literature', 'LCarrol.gz', 'Paradise.Lost.gz', 'aeneid.gz',
                       'arthur.gz', 'cartoon.gz', 'cartoons-olivier.gz', 'charlemagne.gz',
                       'fable.gz', 'iliad.gz', 'myths-legends.gz', 'odyssey.gz', 'sf.gz',
                       'shakespeare.gz', 'tolkien.words.gz'),
                  22: ('movieTV', 'Movies.gz', 'Python.gz', 'Trek.gz'),
                  23: ('music', 'music-classical.gz', 'music-country.gz', 'music-jazz.gz',
                       'music-other.gz', 'music-rock.gz', 'music-shows.gz',
                       'rock-groups.gz'),
                  24: ('names', 'ASSurnames.gz' 'Congress.gz', 'Family-Names.gz',
                       'Given-Names.gz', 'actor-givenname.gz', 'actor-surname.gz',
                       'cis-givenname.gz', 'cis-surname.gz', 'crl-names.gz', 'famous.gz',
                       'fast-names.gz', 'female-names-kantr.gz', 'female-names.gz',
                       'givennames-ol.gz', 'male-names.gz', 'movie-characters.gz',
                       'names.french.gz', 'names.hp.gz', 'other-names.gz',
                       'shakesp-names.gz', 'surnames-ol.gz', 'surnames.finnish.gz',
                       'usenet-names.gz'),
                  25: ('net', 'hosts-txt.gz', 'inet-machines.gz', 'usenet-loginids.gz',
                       'usenet-machines.gz', 'uunet-sites.gz'),
                  26: ('norwegian', 'words.norwegian.gz'),
                  27: ('places', 'Colleges.gz', 'US-counties.gz', 'World.factbook.gz',
                       'Zipcodes.gz', 'places.gz'),
                  28: ('polish', 'words.polish.gz'),
                  29: ('random', 'Ethnologue.gz', 'abbr.gz', 'chars.gz', 'dogs.gz',
                       'drugs.gz', 'junk.gz', 'numbers.gz', 'phrases.gz', 'sports.gz',
                       'statistics.gz'),
                  30: ('religion', 'Koran.gz', 'kjbible.gz', 'norse.gz'),
                  31: ('russian', 'russian.lst.gz', 'russian_words.koi8.gz'),
                  32: ('science', 'Acr-diagnosis.gz', 'Algae.gz', 'Bacteria.gz',
                       'Fungi.gz', 'Microalgae.gz', 'Viruses.gz', 'asteroids.gz',
                       'biology.gz', 'tech.gz'),
                  33: ('spanish', 'words.spanish.gz'),
                  34: ('swahili', 'swahili.gz'),
                  35: ('swedish', 'words.swedish.gz'),
                  36: ('turkish', 'turkish.dict.gz'),
                  37: ('yiddish', 'yiddish.gz'),
                  }

    download_ftp_files(*(arguments[option]))


def alectodb_download():
    """Download csv from alectodb and save into local file as a list of
    usernames and passwords"""
    url = CONFIG['alectourl']
    local_file_name = url.split('/')[-1]

    info("Checking if alectodb is not present...")
    if not os.path.isfile('alectodb.csv.gz'):
        info("Downloading alectodb.csv.gz...")
        web_file = urlopen(url)
        local_file = open(local_file_name, 'w')
        local_file.write(web_file.read())
        web_file.close()
        local_file.close()

    f = gzip.open(local_file_name, 'rb')

    data = csv.reader(f)

    usernames = []
    passwords = []
    for row in data:
        usernames.append(row[5])
        passwords.append(row[6])
    gus = sorted(set(usernames))
    gpa = sorted(set(passwords))
    f.close()

    info("Exporting to alectodb-usernames.txt and alectodb-passwords.txt")
    with open('alectodb-usernames.txt', 'w') as usernames_file:
        usernames_file.write(os.linesep.join(gus))

    with open('alectodb-passwords.txt', 'w') as passwords_file:
        passwords_file.write(os.linesep.join(gpa))
    success("Done.")


def concats(seq, start, stop):
    "Helper function for concatenations."
    for s in seq:
        for num in range(start, stop):
            yield s + str(num)


def komb(seq, start):
    "Helper function for sorting and making combinations."
    for mystr in seq:
        for mystr1 in start:
            yield mystr + mystr1


def leet_replace(s):
    """Replace all instances of a character in a string with their 1337
    counterpart as defined in LEET_CONFIG"""
    for c, n in LEET_CONFIG.items():
        s = s.replace(c, n)
    return s


def improve_dictionary(filename):
    """Implementation of the -w option. Improve a dictionary by
    interactively questioning the user."""
    if not os.path.isfile(filename):
        error('File %s does not exist' % filename)
        exit(1)

    with open(filename) as fajl:
        listic = fajl.readlines()
    linije = len(listic)

    listica = []
    for x in listic:
        listica.extend(x.split())

    print("      *************************************************")
    print("      *                    %s                 *" % colorize('WARNING!!!', 31))
    print("      *         Using large wordlists in some         *")
    print("      *       options bellow is NOT recommended!      *")
    print("      *************************************************\n")

    conts = input_text(
        "Do you want to concatenate all words from wordlist? Y/[N]: ",
        validate='^$|^[yYnN]$'
    ).lower().strip()

    if conts == 'y' and linije > CONFIG['threshold']:
        error(
            "Maximum number of words for concatenation is %i\n"
            "Check configuration file for increasing this number." % CONFIG['threshold']
        )
        sys.exit(1)
    cont = []
    if conts == 'y':
        for cont1 in listica:
            for cont2 in listica:
                if listica.index(cont1) != listica.index(cont2):
                    cont.append(cont1+cont2)

    spechars = []
    spechars1 = input_text(
        "Do you want to add special chars at the end of words? Y/[N]: ",
        validate='^$|^[yYnN]$'
    ).lower()
    if spechars1 == "y":
        for spec1 in CONFIG['chars']:
            spechars.append(spec1)
            for spec2 in CONFIG['chars']:
                spechars.append(spec1+spec2)
                for spec3 in CONFIG['chars']:
                    spechars.append(spec1+spec2+spec3)

    randnum = input_text(
        "Do you want to add some random numbers at the end of words? Y/[N]: ",
        validate='^$|^[yYnN]$'
    ).lower().strip()
    leetmode = input_text(
        "Leet mode? (i.e. leet = 1337) Y/[N]: ",
        validate='^$|^[yYnN]$'
    ).lower().strip()


    kombinacija1 = list(komb(listica, CONFIG['years']))
    kombinacija2 = []
    if conts == "y":
        kombinacija2 = list(komb(cont, CONFIG['years']))
    kombinacija3 = []
    kombinacija4 = []
    if spechars1 == "y":
        kombinacija3 = list(komb(listica, spechars))
        if conts == "y":
            kombinacija4 = list(komb(cont, spechars))
    kombinacija5 = []
    kombinacija6 = []
    if randnum == "y":
        kombinacija5 = list(concats(listica, CONFIG['numfrom'], CONFIG['numto']))
        if conts == "y":
            kombinacija6 = list(concats(cont, CONFIG['numfrom'], CONFIG['numto']))

    info("Now making a dictionary...")
    info("Sorting list and removing duplicates...")

    sets = [set(kombinacija1), set(kombinacija2), set(kombinacija3),
            set(kombinacija4), set(kombinacija5), set(kombinacija6),
            set(listica), set(cont)]

    uniqset = set()
    for s in sets:
        uniqset.update(s)

    unique_lista = sorted(uniqset)
    unique_leet = []
    if leetmode == "y":
        for x in unique_lista:
            unique_leet.append(leet_replace(x))

    unique_list = unique_lista + unique_leet

    unique_list_finished = [x for x in unique_list if CONFIG['wcfrom'] < len(x) < CONFIG['wcto']]
    unique_list_finished.sort()

    file_path = filename + '.cupp.txt'
    with open(file_path, 'w') as f:
        f.write(os.linesep.join(unique_list_finished))

    final_message(file_path, unique_list_finished)

if __name__ == '__main__':
    main()
