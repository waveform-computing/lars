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
Each datatype is given a simple constructor which accepts a string in a common
format (for example, the :func:`date` function which accepts dates in
``YYYY-MM-DD`` format), and returns the converted data.

Most of the time you will not need the functions in this module directly, but
the attributes of the classes are extremely useful for filtering and
transforming log data for output.


Classes
=======

.. autoclass:: Hostname
   :members: address

.. autoclass:: IPv4Address
   :members:

.. autoclass:: IPv4Network
   :members:

.. autoclass:: IPv4Port
   :members:

.. autoclass:: IPv6Address
   :members:

.. autoclass:: IPv6Network
   :members:

.. autoclass:: IPv6Port
   :members:

.. autoclass:: Path
   :members:

.. autoclass:: Url
   :members:


Functions
=========

.. autofunction:: address

.. autofunction:: date

.. autofunction:: datetime

.. autofunction:: hostname

.. autofunction:: network

.. autofunction:: path

.. autofunction:: time

.. autofunction:: url

.. _RFC 1918: http://tools.ietf.org/html/rfc1918
.. _RFC 2373 2.5.2: http://tools.ietf.org/html/rfc2373#section-2.5.2
.. _RFC 2373 2.5.3: http://tools.ietf.org/html/rfc2373#section-2.5.3
.. _RFC 2373 2.7: http://tools.ietf.org/html/rfc2373#section-2.7
.. _RFC 3171: http://tools.ietf.org/html/rfc3171
.. _RFC 3330: http://tools.ietf.org/html/rfc3330
.. _RFC 3513 2.5.6: http://tools.ietf.org/html/rfc3513#section-2.5.6
.. _RFC 3879: http://tools.ietf.org/html/rfc3879
.. _RFC 3927: http://tools.ietf.org/html/rfc3927
.. _RFC 4291: http://tools.ietf.org/html/rfc4291
.. _RFC 4193: http://tools.ietf.org/html/rfc4193
.. _RFC 5735 3: http://tools.ietf.org/html/rfc5735#section-3
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


# XXX Make Py2 str same as Py3
str = type('')


def datetime(s, format='%Y-%m-%d %H:%M:%S'):
    """
    Represents a timestamp.

    Given a string in ISO8601-like format (``YYYY-MM-DD HH:MM:SS``), this
    function returns a datetime value with attributes for the `year`, `month`,
    `day`, `hour`, `minute`, `second`, and optionally the `microsecond`. See
    the Python `datetime`_ reference for full details of available methods.

    :param str s: The string containing the timestamp to parse
    :param str format: Optional string containing the datetime format to parse
    :returns: A :class:`datetime.datetime` object representing the timestamp

    .. _datetime: http://docs.python.org/2/library/datetime.html#datetime
    """
    return dt.datetime.strptime(s, format)


def date(s, format='%Y-%m-%d'):
    """
    Represents a date.

    Given a string in ISO8601 format (``YYYY-MM-DD``), this function returns
    a date value with attributes for the `year`, `month`, and `day`. See the
    Python `date`_ reference for full details of available methods.

    :param str s: The string containing the date to parse
    :param str format: Optional string containing the date format to parse
    :returns: A :class:`datetime.date` object representing the date

    .. _date: http://docs.python.org/2/library/datetime.html#date
    """
    return dt.datetime.strptime(s, format).date()


def time(s, format='%H:%M:%S'):
    """
    Represents a time.

    Given a string with the format ``HH:MM:SS`` (24-hour clock format), this
    function returns a time value with attributes for the ``hour``, ``minute``,
    and ``second``. See the Python `time`_ reference for full details of
    available methods.

    :param str s: The string containing the time to parse
    :param str format: Optional string containing the time format to parse
    :returns: A :class:`datetime.time` object representing the time

    .. _time: http://docs.python.org/2/library/datetime.html#time
    """
    return dt.datetime.strptime(s, format).time()


def path(s):
    """
    Returns a :class:`Path` object for the given string.

    :param str s: The string containing the path to parse
    :returns: A :class:`Path` object representing the path
    """
    return Path(s)


def url(s):
    """
    Returns a :class:`Url` object for the given string.

    :param str s: The string containing the URL to parse
    :returns: A :class:`Url` tuple representing the URL
    """
    return Url(*urlparse.urlparse(s))


def hostname(s):
    """
    Returns a :class:`Hostname` object for the given string.

    :param str s: The string containing the hostname to parse
    :returns: A :class:`Hostname` instance
    """
    return Hostname(s)


def network(s):
    """
    Returns an :class:`IPv4Network` or :class:`IPv6Network` instance for the
    given string.

    :param str s: The string containing the IP network to parse
    :returns: An :class:`IPv4Network` or :class:`IPv6Network` instance
    """
    if isinstance(s, bytes):
        s = str(s)
    try:
        return IPv4Network(s)
    except ValueError:
        pass
    try:
        return IPv6Network(s)
    except ValueError:
        pass
    raise ValueError(
        '%s does not appear to be a valid IPv4 or IPv6 network' % s)


def address(s):
    """
    Returns an :class:`IPv4Address`, :class:`IPv6Address`, :class:`IPv4Port`,
    or :class:`IPv6Port` instance for the given string.

    :param str s: The string containing the IP address to parse
    :returns: An :class:`IPv4Address`, :class:`IPv4Port`, :class:`IPv6Address`,
              or :class:`IPv6Port` instance
    """
    if isinstance(s, bytes):
        s = str(s)
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
class Path(type('')):
    """
    Represents a path.

    This type is returned by the :func:`path` function and represents a path in
    the platform's native format (e.g. with drive and backslash separators on
    Windows, no drive and forward slash separators on Linux/Mac OS X). Numerous
    attributes are provided for extracting any part of the path and querying
    the attributes of the corresponding file (if any) on disk.

    :param str s: The string containing the path to parse
    """

    drive_part_re = re.compile(r'^[a-zA-Z]:$', flags=re.UNICODE)
    file_part_re = re.compile(r'[\x00-\x1f\x7f\\/?:*"><|]', flags=re.UNICODE)

    def __init__(self, s):
        s = str(s)
        # Split the path into drive and path parts
        if sys.platform.startswith('win'):
            drive, path = os.path.splitdrive(s)
            if drive and not self.drive_part_re.match(drive):
                raise ValueError('%s has an invalid drive portion' % s)
        else:
            path = s
        parts = path.split(os.path.sep)
        # For the sake of sanity, raise a ValueError in the case of certain
        # characters which just shouldn't be present in paths
        for part in parts:
            if part and self.file_part_re.search(part):
                raise ValueError(
                    '%s cannot contain control characters or any of '
                    'the following: \\ / ? : * " > < |' % s)
        super(Path, self).__init__(s)

    def relative(self, start=os.curdir):
        """
        Return the path relative to the ``start`` path which defaults to ``.``
        if it is not specified.
        """
        return Path(os.path.relpath(self, start))

    @property
    def abspath(self):
        """
        If the path is relative, this property returns the equivalent absolute
        path, by resolving relative to the current working directory.
        """
        return Path(os.path.abspath(self))

    @property
    def drive(self):
        """
        Returns the drive portion of the path (on Windows), or the blank string
        (on all other supported platforms).
        """
        return Path(os.path.splitdrive(self)[0])

    @property
    def basename(self):
        """
        Returns the filename portion of the path, including its extension (the
        portion after the final dot).
        """
        return Path(os.path.basename(self))

    @property
    def basename_no_ext(self):
        """
        Returns the filename portion of the path, excluding the extension
        after the final dot.
        """
        return Path(os.path.splitext(os.path.basename(self))[0])

    @property
    def dirname(self):
        """
        Returns the path without the final filename portion.
        """
        return Path(os.path.dirname(self))

    @property
    def ext(self):
        """
        Returns the extension of the filename part of the path (the portion
        after the final dot).
        """
        return Path(os.path.splitext(self)[1])

    @property
    def exists(self):
        """
        Returns True if the path currently exists on disk and is not a broken
        symlink.
        """
        return os.path.exists(self)

    @property
    def lexists(self):
        """
        Returns True if the path currently exists on disk even if it is a
        broken symlink.
        """
        return os.path.lexists(self)

    @property
    def atime(self):
        """
        If the path exists on disk, returns the last access time as a
        :class:`datetime.datetime` object, otherwise returns None.
        """
        # XXX What happens when the file doesn't exist?!
        return dt.datetime.utcfromtimestamp(os.path.getatime(self))

    @property
    def mtime(self):
        """
        If the path exists on disk, returns the last modification time as a
        :class:`datetime.datetime` object, otherwise returns None.
        """
        return dt.datetime.utcfromtimestamp(os.path.getmtime(self))

    @property
    def ctime(self):
        """
        If the path exists on disk, returns the last meta-data modification
        time (aka the creation time) as a :class:`datetime.datetime` object,
        otherwise returns None.
        """
        return dt.datetime.utcfromtimestamp(os.path.getctime(self))

    @property
    def size(self):
        """
        If the path exists on disk, returns the size of the file in bytes,
        otherwise returns None.
        """
        return os.path.getsize(self)

    @property
    def isabs(self):
        """
        Returns True if the path is an absolute path.
        """
        return os.path.isabs(self)

    @property
    def isfile(self):
        """
        Returns True if the path represents an existing file on the disk.
        """
        return os.path.isfile(self)

    @property
    def isdir(self):
        """
        Returns True if the path represents an existing directory on the disk.
        """
        return os.path.isdir(self)

    @property
    def islink(self):
        """
        Returns True if the path represents a symlink on the disk.
        """
        return os.path.islink(self)

    @property
    def ismount(self):
        """
        Returns True if the path represents an active mount-point on the disk.
        """
        return os.path.ismount(self)

    @property
    def normcase(self):
        """
        Returns the lowercase version of the path on Windows, or the path
        unchanged on Linux or Mac OS X.
        """
        return Path(os.path.normcase(self))

    @property
    def normpath(self):
        """
        Returns the path with redundant sections (``.`` for the current
        directory, doubled slashes, etc.) removed.
        """
        return Path(os.path.normpath(self))

    @property
    def realpath(self):
        """
        Returns the path after resolution of symlinks. Note that this may
        change the behaviour of the path on certain platforms.
        """
        return Path(os.path.realpath(self))


class Url(namedtuple('Url', 'scheme netloc path params query fragment'), urlparse.ResultMixin):
    """
    Represents a URL.

    This type is returned by the :func:`url` function and represents the parts
    of the URL.

    .. attribute:: scheme

       The scheme of the URL, before the first ``:``

    .. attribute:: netloc

       The "network location" of the URL, comprising the hostname and port
       (separated by a colon), and historically the username and password
       (prefixed to the hostname and separated with an ampersand)

    .. attribute:: path

       The path of the URL from the first slash after the network location

    .. attribute:: params

       The parameters of the URL

    .. attribute:: query

       The query string of the URL from the first question-mark in the path

    .. attribute:: fragment

       The fragment of the URL from the last hash-mark to the end of the URL

    Additionally, the following attributes can be used to separate out the
    various parts of the :attr:`netloc` attribute:

    .. attribute:: username

       The username (historical, rare to see this used on the modern web)

    .. attribute:: password

       The password (historical, almost unheard of on the modern web as it's
       extremely insecure to include credentials in the URL)

    .. attribute:: hostname

       The hostname from the network location. This attribute returns a
       :class:`Hostname` object which can be used to resolve the hostname into
       an IP address if required.

    .. attribute:: port

       The optional network port
    """

    __slots__ = ()

    def geturl(self):
        return urlparse.urlunparse(self)

    def __str__(self):
        return self.geturl()

    @property
    def hostname(self):
        return hostname(super(Url, self).hostname)


@total_ordering
class Hostname(str):
    """
    Represents an Internet hostname and provides attributes for DNS resolution.

    This type is returned by the :func:`hostname` function and represents a DNS
    hostname. The :attr:`address` property allows resolution of the hostname
    to an IP address.

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
        """
        Attempts to resolve the hostname into an IPv4 or IPv6 address
        (returning an :class:`IPv4Address` or :class:`IPv6Address` object
        repsectively). The result of the DNS query (including negative lookups
        is cached, so repeated queries for the same hostname should be
        extremely fast.
        """
        ipaddr = dns.to_address(self)
        if ipaddr is not None:
            return address(ipaddr)


class IPv4Address(ipaddress.IPv4Address):
    """
    Represents an IPv4 address.

    This type is returned by the :func:`address` function and represents an
    IPv4 address and provides various attributes and comparison operators
    relevant to such addresses.

    For example, to test whether an address belongs to particular network you
    can use the ``in`` operator with the result of the :func:`network`
    function::

        address('192.168.0.64') in network('192.168.0.0/16')

    The :attr:`hostname` attribute will perform reverse DNS resolution to
    determine a hostname associated with the address (if any). The result of
    the query (including negative lookups) is cached so subsequent queries of
    the same address should be extermely rapid.

    If the :mod:`geoip` module has been initialized with a database, the
    GeoIP-related attributes :attr:`country`, :attr:`region`, :attr:`city`, and
    :attr:`coords` will return the country, region, city and a (longitude,
    latitude) tuple respectively.

    .. attribute:: compressed

        Returns the shorthand version of the IP address as a string (this is
        the default string conversion).

    .. attribute:: exploded

        Returns the longhand version of the IP address as a string.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 3927`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 3330`_ for
        details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        3171`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 1918`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 5735 3`_ for
        details.

    .. attribute:: packed

        Returns the binary representation of this address.
    """

    @property
    def country(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called to initialize
        a GeoIP database, returns the country of the address.
        """
        return geoip.country_code_by_addr(self.compressed)

    @property
    def region(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        region-level (or lower) GeoIP database, returns the region of the
        address.
        """
        return geoip.region_by_addr(self.compressed)

    @property
    def city(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP database, returns the city of the address.
        """
        return geoip.city_by_addr(self.compressed)

    @property
    def coords(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr(self.compressed)

    @property
    def hostname(self):
        """
        Performs a reverse DNS lookup to attempt to determine a hostname for
        the address. Lookups (including negative lookups) are cached so that
        repeated lookups are extremely quick. Returns a :class:`Hostname`
        object if the lookup is successful, or None.
        """
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv6Address(ipaddress.IPv6Address):
    """
    Represents an IPv6 address.

    This type is returned by the :func:`address` function and represents an
    IPv6 address and provides various attributes and comparison operators
    relevant to such addresses.

    For example, to test whether an address belongs to particular network you
    can use the ``in`` operator with the result of the :func:`network`
    function::

        address('::1') in network('::/16')

    The :attr:`hostname` attribute will perform reverse DNS resolution to
    determine a hostname associated with the address (if any). The result of
    the query (including negative lookups) is cached so subsequent queries of
    the same address should be extermely rapid.

    If the :mod:`geoip` module has been initialized with a database, the
    GeoIP-related attributes :attr:`country`, :attr:`region`, :attr:`city`, and
    :attr:`coords` will return the country, region, city and a (longitude,
    latitude) tuple respectively.

    .. attribute:: compressed

        Returns the shorthand version of the IP address as a string (this is
        the default string conversion).

    .. attribute:: exploded

        Returns the longhand version of the IP address as a string.

    .. attribute:: ipv4_mapped

        Returns the IPv4 mapped address if the IPv6 address is a v4 mapped
        address, or ``None`` otherwise.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_site_local

        Returns True if the address is reserved for site-local.

        Note that the site-local address space has been deprecated by `RFC
        3879`_.  Use :attr:`is_private` to test if this address is in the space
        of unique local addresses as defined by `RFC 4193`_. See `RFC 3513
        2.5.6`_ for details.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.

    .. attribute:: packed

        Returns the binary representation of this address.

    .. attribute:: sixtofour

        Returns the IPv4 6to4 embedded address if present, or ``None`` if the
        address doesn't appear to contain a 6to4 embedded address.

    .. attribute:: teredo

        Returns a ``(server, client)`` tuple  of embedded Teredo IPs, or
        ``None`` if the address doesn't appear to be a Teredo address (doesn't
        start with ``2001::/32``).
    """

    @property
    def country(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called to initialize
        a GeoIP IPv6 database, returns the country of the address.
        """
        return geoip.country_code_by_addr_v6(self.__str__())

    @property
    def region(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        region-level (or lower) GeoIP IPv6 database, returns the region of the
        address.
        """
        return geoip.region_by_addr_v6(self.__str__())

    @property
    def city(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP IPv6 database, returns the city of the address.
        """
        return geoip.city_by_addr_v6(self.__str__())

    @property
    def coords(self):
        """
        If :func:`~www2csv.geoip.init_database` has been called with a
        city-level GeoIP IPv6 database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr_v6(self.__str__())

    @property
    def hostname(self):
        """
        Performs a reverse DNS lookup to attempt to determine a hostname for
        the address. Lookups (including negative lookups) are cached so that
        repeated lookups are extremely quick. Returns a :class:`Hostname`
        object if the lookup is successful, or None.
        """
        s = self.compressed
        result = dns.from_address(s)
        if result == s:
            return None
        return Hostname(result)


class IPv4Network(ipaddress.IPv4Network):
    """
    This type is returned by the :func:`network` function. This class represents
    and manipulates 32-bit IPv4 networks.

    Attributes: [examples for IPv4Network('192.0.2.0/27')]

        * :attr:`network_address`: ``IPv4Address('192.0.2.0')``
        * :attr:`hostmask`: ``IPv4Address('0.0.0.31')``
        * :attr:`broadcast_address`: ``IPv4Address('192.0.2.32')``
        * :attr:`netmask`: ``IPv4Address('255.255.255.224')``
        * :attr:`prefixlen`: ``27``

    .. method:: address_exclude(other)

        Remove an address from a larger block.

        For example::

            addr1 = network('192.0.2.0/28')
            addr2 = network('192.0.2.1/32')
            addr1.address_exclude(addr2) = [
                IPv4Network('192.0.2.0/32'), IPv4Network('192.0.2.2/31'),
                IPv4Network('192.0.2.4/30'), IPv4Network('192.0.2.8/29'),
                ]

        :param other: An IPv4Network object of the same type.
        :returns: An iterator of the IPv4Network objects which is self minus
                  other.

    .. method:: compare_networks(other)

        Compare two IP objects.

        This is only concerned about the comparison of the integer
        representation of the network addresses. This means that the host bits
        aren't considered at all in this method. If you want to compare host
        bits, you can easily enough do a ``HostA._ip < HostB._ip``.

        :param other: An IP object.
        :returns: -1, 0, or 1 for less than, equal to or greater than
                  respectively.

    .. method:: hosts()

        Generate iterator over usable hosts in a network.

        This is like :meth:`__iter__` except it doesn't return the network
        or broadcast addresses.

    .. method:: overlaps(other)

        Tells if self is partly contained in *other*.

    .. method:: subnets(prefixlen_diff=1, new_prefix=None)

        The subnets which join to make the current subnet.

        In the case that self contains only one IP (self._prefixlen == 32 for
        IPv4 or self._prefixlen == 128 for IPv6), yield an iterator with just
        ourself.

        :param int prefixlen_diff: An integer, the amount the prefix length
            should be increased by. This should not be set if *new_prefix* is
            also set.
        :param int new_prefix: The desired new prefix length. This must be a
            larger number (smaller prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An iterator of IPv(4|6) objects.

    .. method:: supernet(prefixlen_diff=1, new_prefix=None)

        The supernet containing the current network.

        :param int prefixlen_diff: An integer, the amount the prefix length of
            the network should be decreased by.  For example, given a ``/24``
            network and a prefixlen_diff of ``3``, a supernet with a ``/21``
            netmask is returned.
        :param int new_prefix: The desired new prefix length. This must be a
            smaller number (larger prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An IPv4Network object.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.
    """


class IPv4Port(IPv4Address):
    """
    Represents an IPv4 address and port number.

    This type is returned by the :func:`address` function and represents an
    IPv4 address and port number. Other than this, all properties of the base
    :class:`IPv4Address` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
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
    Represents an IPv6 address and port number.

    This type is returned by the :func:`address` function an represents an IPv6
    address and port number. The string representation of an IPv6 address with
    port necessarily wraps the address portion in square brakcets as otherwise
    the port number will make the address ambiguous. Other than this, all
    properties of the base :class:`IPv46ddress` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
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


class IPv6Network(ipaddress.IPv6Network):
    """
    This type is returned by the :func:`network` function. This class represents
    and manipulates 128-bit IPv6 networks.

    .. method:: address_exclude(other)

        Remove an address from a larger block.

        For example::

            addr1 = network('192.0.2.0/28')
            addr2 = network('192.0.2.1/32')
            addr1.address_exclude(addr2) = [
                IPv4Network('192.0.2.0/32'), IPv4Network('192.0.2.2/31'),
                IPv4Network('192.0.2.4/30'), IPv4Network('192.0.2.8/29'),
                ]

        :param other: An IPv4Network object of the same type.
        :returns: An iterator of the IPv4Network objects which is self minus
                  other.

    .. method:: compare_networks(other)

        Compare two IP objects.

        This is only concerned about the comparison of the integer
        representation of the network addresses. This means that the host bits
        aren't considered at all in this method. If you want to compare host
        bits, you can easily enough do a ``HostA._ip < HostB._ip``.

        :param other: An IP object.
        :returns: -1, 0, or 1 for less than, equal to or greater than
                  respectively.

    .. method:: hosts()

        Generate iterator over usable hosts in a network.

        This is like :meth:`__iter__` except it doesn't return the network
        or broadcast addresses.

    .. method:: overlaps(other)

        Tells if self is partly contained in *other*.

    .. method:: subnets(prefixlen_diff=1, new_prefix=None)

        The subnets which join to make the current subnet.

        In the case that self contains only one IP (self._prefixlen == 32 for
        IPv4 or self._prefixlen == 128 for IPv6), yield an iterator with just
        ourself.

        :param int prefixlen_diff: An integer, the amount the prefix length
            should be increased by. This should not be set if *new_prefix* is
            also set.
        :param int new_prefix: The desired new prefix length. This must be a
            larger number (smaller prefix) than the existing prefix. This
            should not be set if *prefixlen_diff* is also set.
        :returns: An iterator of IPv(4|6) objects.

    .. method:: supernet(prefixlen_diff=1, new_prefix=None)

        The supernet containing the current network.

        :param int prefixlen_diff: An integer, the amount the prefix length of
              the network should be decreased by.  For example, given a ``/24``
              network and a prefixlen_diff of ``3``, a supernet with a ``/21``
              netmask is returned.
        :param int new_prefix: The desired new prefix length. This must be a
              smaller number (larger prefix) than the existing prefix. This
              should not be set if *prefixlen_diff* is also set.
        :returns: An IPv4Network object.

    .. attribute:: is_link_local

        Returns True if the address is reserved for link-local. See `RFC 4291`_
        for details.

    .. attribute:: is_loopback

        Returns True if the address is a loopback address. See `RFC 2373
        2.5.3`_ for details.

    .. attribute:: is_multicast

        Returns True if the address is reserved for multicast use.  See `RFC
        2373 2.7`_ for details.

    .. attribute:: is_private

        Returns True if this address is allocated for private networks. See
        `RFC 4193`_ for details.

    .. attribute:: is_reserved

        Returns True if the address is otherwise IETF reserved.

    .. attribute:: is_unspecified

        Returns True if the address is unspecified. See `RFC 2373 2.5.2`_ for
        details.
    """
