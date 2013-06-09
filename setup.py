#!/usr/bin/env python
# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Dave Hughes <dave@waveform.org.uk>
# Copyright (c) 2013 Mime Consulting Ltd. <info@mimeconsulting.co.uk>
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (
    #unicode_literals,
    print_function,
    absolute_import,
    division,
    )

import sys
import os
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from utils import description, get_version

if not sys.version_info >= (2, 7):
    raise ValueError('This package requires Python 2.7 or above')

HERE = os.path.abspath(os.path.dirname(__file__))

# Workaround <http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html>
try:
    import multiprocessing
except ImportError:
    pass

# Workaround <http://bugs.python.org/issue10945>
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {True: enc}.get(name=='mbcs')
    codecs.register(func)

# All meta-data is defined as global variables so that other modules can query
# it easily without having to wade through distutils nonsense
NAME         = 'lars'
DESCRIPTION  = 'A framework for converting web-logs into various formats'
KEYWORDS     = ['web', 'www', 'logs', 'database']
AUTHOR       = 'Dave Hughes'
AUTHOR_EMAIL = 'dave@waveform.org.uk'
MANUFACTURER = 'waveform'
URL          = 'http://github.com/waveform80/lars'

REQUIRES = [
    'ipaddress', # Google's IPv4/IPv6 parsing library (part of stdlib in py3k)
    'pygeoip',   # Pure Python GeoIP library
    ]

EXTRA_REQUIRES = {
    }

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Topic :: Internet :: WWW/HTTP :: Site Management',
    'Topic :: Text Processing',
    ]

ENTRY_POINTS = {
    }

PACKAGES = [
    'lars',
    ]

PACKAGE_DATA = {
    }


# Add a py.test based "test" command
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '--cov', NAME,
            '--cov-report', 'term-missing',
            '--cov-report', 'html',
            '--cov-config', 'coverage.cfg',
            'tests',
            ]
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


def main():
    setup(
        name                 = NAME,
        version              = get_version(os.path.join(HERE, NAME, '__init__.py')),
        description          = DESCRIPTION,
        long_description     = description(os.path.join(HERE, 'README.rst')),
        classifiers          = CLASSIFIERS,
        author               = AUTHOR,
        author_email         = AUTHOR_EMAIL,
        url                  = URL,
        keywords             = ' '.join(KEYWORDS),
        packages             = PACKAGES,
        package_data         = PACKAGE_DATA,
        platforms            = 'ALL',
        install_requires     = REQUIRES,
        extras_require       = EXTRA_REQUIRES,
        zip_safe             = True,
        entry_points         = ENTRY_POINTS,
        tests_require        = ['pytest', 'pytest-cov', 'mock'],
        cmdclass             = {'test': PyTest},
        )

if __name__ == '__main__':
    main()
