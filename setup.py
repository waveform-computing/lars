#!/usr/bin/env python
# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Copyright (c) 2013-2017 Dave Jones <dave@waveform.org.uk>
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

"A framework for converting web-logs into various formats"

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
str = type('')

import os
import sys
from setuptools import setup, find_packages

if sys.version_info[0] == 2:
    if not sys.version_info >= (2, 7):
        raise ValueError('This package requires Python 2.7 or above')
elif sys.version_info[0] == 3:
    if not sys.version_info >= (3, 2):
        raise ValueError('This package requires Python 3.2 or above')
else:
    raise ValueError('Unrecognized major version of Python')

HERE = os.path.abspath(os.path.dirname(__file__))

# Workaround <http://bugs.python.org/issue10945>
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    func = lambda name, enc=ascii: {True: enc}.get(name=='mbcs')
    codecs.register(func)

# Workaround <http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html>
try:
    import multiprocessing
except ImportError:
    pass

__project__      = 'lars'
__version__      = '1.0'
__authors__      = ['Dave Jones', 'Mime Consulting Ltd.']
__author__       = __authors__[0]
__author_email__ = 'dave@waveform.org.uk'
__url__          = 'http://github.com/waveform-computing/lars'
__platforms__    = 'ALL'

__classifiers__  = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: Internet :: WWW/HTTP :: Site Management',
    'Topic :: Text Processing',
    ]

__keywords__ = [
    'web',
    'www',
    'logs',
    'database',
    ]

__requires__ = [
    'pygeoip',   # Pure Python GeoIP library
    ]

__extra_requires__ = {
    'doc': ['sphinx'],
    'test': ['pytest', 'coverage', 'mock'],
    }

__entry_points__ = {
    }

__dependency_links__ = []

if sys.version_info[:2] < (3, 0):
    # Add particular down-level versions for compatibility with legacy versions
    # of Python; hilariously 2.7 is now better supported than 3.2 or 3.3...
    __requires__.append('ipaddr')
    __requires__.append('backports.csv')
elif sys.version_info[:2] == (3, 2):
    # The version of ipaddr on PyPI is incompatible with Python 3.2; use a
    # private fork of it instead
    __requires__.append('setuptools==18.4')
    __requires__.append('pip==7.0.0')
    __requires__.append('ipaddr==2.1.11py3.2')
    __dependency_links__.append('git+https://github.com/waveform-computing/ipaddr#egg=ipaddr-2.1.11py3.2')
    __extra_requires__['doc'].extend([
        'Jinja2<2.7',
        'MarkupSafe<0.16',
        ])
    __extra_requires__['test'].remove('pytest')
    __extra_requires__['test'].append('pytest==2.9.2')
    __extra_requires__['test'].remove('coverage')
    __extra_requires__['test'].append('coverage<4.0dev')
    __extra_requires__['test'].append('attrs==16.2.0')
elif sys.version_info[:2] == (3, 3):
    __requires__.append('setuptools==30.1')


def main():
    import io
    with io.open(os.path.join(HERE, 'README.rst'), 'r') as readme:
        setup(
            name                 = __project__,
            version              = __version__,
            description          = __doc__,
            long_description     = readme.read(),
            classifiers          = __classifiers__,
            author               = __author__,
            author_email         = __author_email__,
            url                  = __url__,
            license              = [
                c.rsplit('::', 1)[1].strip()
                for c in __classifiers__
                if c.startswith('License ::')
                ][0],
            keywords             = __keywords__,
            packages             = find_packages(),
            include_package_data = True,
            platforms            = __platforms__,
            install_requires     = __requires__,
            extras_require       = __extra_requires__,
            tests_require        = __extra_requires__.get('test', []),
            entry_points         = __entry_points__,
            dependency_links     = __dependency_links__,
            )


if __name__ == '__main__':
    main()
