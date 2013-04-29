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

"""
Provides data-types commonly used in log files.

This module wraps various Python data-types which are commonly found in log
files to provide them with default string coercions and enhanced attributes.
Specifically, the following types are wrapped or introduced:

  * date, time, and datetime from the datetime module
  * urlparse from the urlparse module (as "url")
  * a "filename" type derived from "str" which has os.path based attributes

Reference
=========

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import os
from collections import namedtuple
import datetime as dt
import urlparse



class Url(namedtuple('ParseResult', 'scheme netloc path params query fragment'), urlparse.ResultMixin):
    """
    Redefined version of the urlparse result which adds a :meth:`__str__`
    method. See :func:`uri_parse` for more information.
    """

    __slots__ = ()

    def geturl(self):
        return urlparse.urlunparse(self)

    def __str__(self):
        return self.geturl()


def url(s):
    """
    Parse a URL.

    This is a variant on the urlparse.urlparse function. The result type has
    been extended to include a :meth:`Url.__str__` method which outputs the
    reconstructed URL.

    :param str s: The string containing the URL to parse
    :returns: A :class:`Url` tuple representing the URL
    """
    return Url(*urlparse.urlparse(s))


def date(s, format='%Y-%m-%d'):
    """
    Parse a date.

    Parses a string containing a date, in ISO8601 format by default
    (YYYY-MM-DD), returning a datetime.date type.

    :param str s: The string containing the date to parse
    :returns: A datetime.date object representing the date
    """
    return datetime.datetime.strptime(s, format).date()


def time(s, format='%H:%M:%S'):
    """
    Parse a time.

    Parses a string containing a time, in ISO8601 format by default (HH:MM:SS),
    returning a datetime.time type.

    :param str s: The string containing the time to parse
    :returns: A datetime.time object representing the time
    """
    return datetime.datetime.strptime(s, format).time()


# Py3k: The base class of type('') is simply a short-hand way of saying unicode
# on py2 (because of the future import at the top of the module) and str on py3
_filepart_re = re.compile(r'[^\x00-\x1f\x7f\\/?:*"><|]', flags=re.UNICODE)
class Filename(type('')):
    """
    Represents a filename.

    Derivative of unicode (on Python 2) or str (on Python 3) which is intended
    to represent a filename. Provides methods and attributes derived from the
    functions available in the :module:`os.path` module.
    
    For the sake of sanity, the class initializer will raise ValueError in the
    case of characters which are invalid in Windows filenames (POSIX permits
    insane things like control characters in filenames, but that's no reason to
    make it easy).

    :param str s: The string containing the filename
    """

    def __init__(self, s):
        # Implicitly expand ~ if it occurs at the start of the string
        s = os.path.expanduser(s)
        # For the sake of sanity, raise a ValueError in the case of certain
        # characters which just shouldn't be present in filenames
        for part in s.split(os.path.sep):
            if part and _filepart_re.search(part):
                raise ValueError(
                    '%s cannot contain control characters or any of '
                    'the following: \\ / ? : * " > < |' % s)

    @property
    def abspath(self):
        return Filename(os.path.abspath(self))

    @property
    def basename(self):
        return Filename(os.path.basename(self))

    @property
    def dirname(self):
        return Filename(os.path.dirname(self))

    @property
    def exists(self):
        return os.path.exists(self)

    @property
    def lexists(self):
        return os.path.lexists(self)

    @property
    def atime(self):
        return datetime.utcfromtimestamp(os.path.getatime(self))

    @property
    def mtime(self):
        return datetime.utcfromtimestamp(os.path.getmtime(self))

    @property
    def ctime(self):
        return datetime.utcfromtimestamp(os.path.getctime(self))

    @property
    def size(self):
        return os.path.getsize(self)

    @property
    def isabs(self):
        return os.path.isabs(self)

    @property
    def isfile(self):
        return os.path.isfile(self)

    @property
    def isdir(self):
        return os.path.isdir(self)

    @property
    def islink(self):
        return os.path.islink(self)

    @property
    def ismount(self):
        return os.path.ismount(self)

    @property
    def normcase(self):
        return Filename(os.path.normcase(self))

    @property
    def normpath(self):
        return Filename(os.path.normpath(self))

    @property
    def realpath(self):
        return Filename(os.path.realpath(self))

    @property
    def split(self):
        head, tail = os.path.split(self)
        return (Filename(head), Filename(tail))

    @property
    def splitdrive(self):
        drive, tail = os.path.splitdrive(self)
        return (Filename(drive), Filename(tail))

    def join(self, *parts):
        return Filename(os.path.join(self, *parts))

    def relative(self, start=os.curdir):
        return Filename(os.path.relpath(self, start))


def filename(s):
    return Filename(s)
