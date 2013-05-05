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

import sys
import os
import re
import datetime as dt
import urlparse
import ipaddress
from collections import namedtuple
from functools import total_ordering

from www2csv import geoip, dns



def date(s, format='%Y-%m-%d'):
    """
    Parse a date.

    Parses a string containing a date, in ISO8601 format by default
    (YYYY-MM-DD), returning a datetime.date type.

    :param str s: The string containing the date to parse
    :returns: A datetime.date object representing the date
    """
    return dt.datetime.strptime(s, format).date()


def time(s, format='%H:%M:%S'):
    """
    Parse a time.

    Parses a string containing a time, in ISO8601 format by default (HH:MM:SS),
    returning a datetime.time type.

    :param str s: The string containing the time to parse
    :returns: A datetime.time object representing the time
    """
    return dt.datetime.strptime(s, format).time()


def filename(s):
    """
    Parse a filename.

    Parses a filename, returning a Filename object which provides various
    os.path based attributes for further manipulation.

    :param str s: The string containing the filename to parse
    :returns: A Filename object representing the filename
    """
    return Filename(s)


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


def hostname(s):
    """
    Parse a hostname.

    The result is a Hostname object which can be used to resolve the parsed
    hostname into an IPv4Address or IPv6Address object which can then be used
    to retrieve further details about the host via the GeoIP attributes.

    :param str s: The string containing the hostname to parse
    :returns: A Hostname instance
    """
    return Hostname(s)


def address(s):
    """
    Parse an IP address and optional port.

    This is a variant on the ipaddress module's ip_address function which
    uses the derived classes IPv4Port and IPv6Port in order to permit an
    optional port specification to be included in the parsed string.

    :param str s: The string containing the IP address to parse
    :returns: An IPv4Address, IPv4Port, IPv6Address, or IPv6Port instance
    """
    if isinstance(s, bytes):
        s = type('')(s)
    try:
        return IPv4Address(s)
    except ValueError:
        pass
    try:
        return IPv6Address(s)
    except ValueError:
        pass
    try:
        return IPv4Port(s)
    except ValueError:
        pass
    try:
        return IPv6Port(s)
    except ValueError:
        pass
    raise ValueError(
        '%s does not appear to be a valid IPv4 or IPv6 address' % s)


# Py3k: The base class of type('') is simply a short-hand way of saying unicode
# on py2 (because of the future import at the top of the module) and str on py3
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

    file_part_re = re.compile(r'[\x00-\x1f\x7f\\/?:*"><|]', flags=re.UNICODE)

    def __init__(self, s):
        # Split the path into drive and path parts
        parts = []
        if sys.platform.startswith('win'):
            drive, path = os.path.splitdrive(s)
            if drive:
                parts.append(drive)
        else:
            path = s
        parts.extend(s.split(os.path.sep))
        # For the sake of sanity, raise a ValueError in the case of certain
        # characters which just shouldn't be present in filenames
        for part in parts:
            if part and self.file_part_re.search(part):
                raise ValueError(
                    '%s cannot contain control characters or any of '
                    'the following: \\ / ? : * " > < |' % s)
        super(Filename, self).__init__(s)

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
        return dt.datetime.utcfromtimestamp(os.path.getatime(self))

    @property
    def mtime(self):
        return dt.datetime.utcfromtimestamp(os.path.getmtime(self))

    @property
    def ctime(self):
        return dt.datetime.utcfromtimestamp(os.path.getctime(self))

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

    def relative(self, start=os.curdir):
        return Filename(os.path.relpath(self, start))


class Url(namedtuple('ParseResult', 'scheme netloc path params query fragment'), urlparse.ResultMixin):
    """
    Redefined version of the urlparse result which adds a :meth:`__str__`
    method. See :func:`url` for more information.
    """

    __slots__ = ()

    def geturl(self):
        return urlparse.urlunparse(self)

    def __str__(self):
        return self.geturl()


@total_ordering
class Hostname(type('')):
    """
    Represents an Internet hostname, and provides methods for DNS resolution.

    :param str hostname: The hostname to parse
    """

    name_part_re = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', flags=re.UNICODE)

    def __init__(self, s):
        if len(s) > 255:
            raise ValueError('DNS name %s is longer than 255 chars' % hostname)
        for part in s.split('.'):
            # XXX What about IPv6 addresses? Check with address_parse?
            if not self.name_part_re.match(part):
                raise ValueError('DNS label %s is invalid' % part)
        super(Hostname, self).__init__(s)

    @property
    def address(self):
        ipaddr = dns.to_address(self)
        if ipaddr is not None:
            return address(ipaddr)


class IPv4Address(ipaddress.IPv4Address):
    """
    Derivative of IPv4Address that provides GeoIP attributes.
    """

    @property
    def country(self):
        return geoip.country_code_by_addr(self.compressed)

    @property
    def region(self):
        return geoip.region_by_addr(self.compressed)

    @property
    def city(self):
        return geoip.city_by_addr(self.compressed)

    @property
    def coords(self):
        return geoip.coords_by_addr(self.compressed)

    @property
    def hostname(self):
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv6Address(ipaddress.IPv6Address):
    """
    Derivative of IPv6Address that provides GeoIP attributes.
    """

    @property
    def country(self):
        return geoip.country_code_by_addr_v6(self.__str__())

    @property
    def region(self):
        return geoip.region_by_addr_v6(self.__str__())

    @property
    def city(self):
        return geoip.city_by_addr_v6(self.__str__())

    @property
    def coords(self):
        return geoip.coords_by_addr_v6(self.__str__())

    @property
    def hostname(self):
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv4Port(IPv4Address):
    """
    Derivative of IPv4Address that adds a port specification.

    :param str address: The address and port to parse.
    """

    def __init__(self, address):
        port = None
        if ':' in address:
            address, port = address.rsplit(':', 1)
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError('Invalid port %d' % port)
        super(IPv4Port, self).__init__(address)
        self.port = port

    def __str__(self):
        result = super(IPv4Port, self).__str__()
        if self.port is not None:
            return '%s:%d' % (result, self.port)
        return result


class IPv6Port(IPv6Address):
    """
    Derivative of IPv6Address that adds a port specification.

    :param str address: The address (and optional port) to parse
    """

    def __init__(self, address):
        address, sep, port = address.rpartition(':')
        if port.endswith(']'): # [IPv6addr]
            address = '%s:%s' % (address[1:], port[:-1])
            port = None
        elif address.endswith(']'): # [IPv6addr]:port
            address = address[1:-1]
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError('Invalid port %d' % port)
        else: # IPv6addr
            address = '%s:%s' % (address, port)
            port = None
        super(IPv6Port, self).__init__(address)
        self.port = port

    def __str__(self):
        result = super(IPv6Port, self).__str__()
        if self.port is not None:
            return '[%s]:%d' % (result, self.port)
        return result

