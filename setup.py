#!/usr/bin/env python
# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Dave Hughes
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

import os
from setuptools import setup, find_packages
from utils import description, get_version, require_python

HERE = os.path.abspath(os.path.dirname(__file__))

# Workaround <http://bugs.python.org/issue10945>
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {True: enc}.get(name=='mbcs')
    codecs.register(func)

require_python(0x020600f0)

# All meta-data is defined as global variables so that other modules can query
# it easily without having to wade through distutils nonsense
NAME         = 'www2csv'
DESCRIPTION  = 'Tools for converting web-logs into database-friendly files'
KEYWORDS     = ['web', 'www', 'logs', 'database']
AUTHOR       = 'Dave Hughes'
AUTHOR_EMAIL = 'dave@waveform.org.uk'
MANUFACTURER = 'waveform'
URL          = 'https://github.com/waveform80/www2csv'

REQUIRES = [
    'ipaddress', # Google's IPv4/IPv6 parsing library (part of stdlib in py3k)
    ]

EXTRA_REQUIRES = {
    }

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Multimedia :: Graphics',
    'Topic :: Scientific/Engineering',
    ]

ENTRY_POINTS = {
    }

PACKAGES = [
    'www2csv',
    ]

PACKAGE_DATA = {
    }


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
        test_suite           = NAME,
        entry_points         = ENTRY_POINTS,
        )

if __name__ == '__main__':
    main()
