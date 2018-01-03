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
#
#
# The documentation for the IPv4Address, IPv4Network, IPv6Address, and
# IPv6Network classes in this module are derived from the ipaddress
# documentation sources which are subject to the following copyright and are
# licensed to the PSF under the contributor agreement which makes them subject
# to the PSF license stated above.
#
# Copyright (c) 2007 Google Inc.

"""
Defines the IP address related parts of :mod:`lars.datatypes`.
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import re
from functools import total_ordering
try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress

from lars import dns
from lars import geoip

native_str = str  # pylint: disable=invalid-name
str = type('')  # pylint: disable=redefined-builtin,invalid-name


def hostname(s):
    """
    Returns a :class:`Hostname`, :class:`IPv4Address`, or :class:`IPv6Address`
    object for the given string depending on whether it represents an IP
    address or a hostname.

    :param str s: The string containing the hostname to parse
    :returns: A :class:`Hostname`, :class:`IPv4Address`, or
              :class:`IPv6Address` instance
    """
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    try:
        return IPv4Address(s)
    except ValueError:
        pass
    try:
        return IPv6Address(s)
    except ValueError:
        pass
    return Hostname(s)


def network(s):
    """
    Returns an :class:`IPv4Network` or :class:`IPv6Network` instance for the
    given string.

    :param str s: The string containing the IP network to parse
    :returns: An :class:`IPv4Network` or :class:`IPv6Network` instance
    """
    if isinstance(s, bytes):
        s = s.decode('utf-8')
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
        s = s.decode('utf-8')
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


@total_ordering
class Hostname(str):
    """
    Represents an Internet hostname and provides attributes for DNS resolution.

    This type is returned by the :func:`hostname` function and represents a DNS
    hostname. The :attr:`address` property allows resolution of the hostname
    to an IP address.

    :param str hostname: The hostname to parse
    """

    name_part_re = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$',
                              flags=re.UNICODE)

    def __init__(self, s):
        if len(s) > 255:
            raise ValueError('DNS name %s is longer than 255 chars' % hostname)
        for part in s.split('.'):
            # XXX What about IPv6 addresses? Check with address_parse?
            if not self.name_part_re.match(part):
                raise ValueError('DNS label %s is invalid' % part)
        super(Hostname, self).__init__()

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
    # pylint: disable=too-many-ancestors
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

    If the :mod:`lars.geoip` module has been initialized with a database, the
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
    # pylint: disable=too-many-ancestors

    @property
    def country(self):
        """
        If :func:`~lars.geoip.init_databases` has been called to initialize
        a GeoIP database, returns the country of the address.
        """
        return geoip.country_code_by_addr(self)

    @property
    def region(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        region-level (or lower) GeoIP database, returns the region of the
        address.
        """
        return geoip.region_by_addr(self)

    @property
    def city(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        city-level GeoIP database, returns the city of the address.
        """
        return geoip.city_by_addr(self)

    @property
    def coords(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        city-level GeoIP database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr(self)

    @property
    def isp(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with an ISP level
        database, returns the ISP that provides connectivity for the address.
        """
        return geoip.isp_by_addr(self)

    @property
    def org(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with an
        organisation level database, returns the name of the organisation the
        address belongs to.
        """
        return geoip.org_by_addr(self)

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
    # pylint: disable=too-many-ancestors
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

    If the :mod:`lars.geoip` module has been initialized with a database, the
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
        If :func:`~lars.geoip.init_databases` has been called to initialize
        a GeoIP IPv6 database, returns the country of the address.
        """
        return geoip.country_code_by_addr(self)

    @property
    def region(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        region-level (or lower) GeoIP IPv6 database, returns the region of the
        address.
        """
        return geoip.region_by_addr(self)

    @property
    def city(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        city-level GeoIP IPv6 database, returns the city of the address.
        """
        return geoip.city_by_addr(self)

    @property
    def coords(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with a
        city-level GeoIP IPv6 database, returns a (longitude, latitude) tuple
        describing the approximate location of the address.
        """
        return geoip.coords_by_addr(self)

    @property
    def isp(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with an ISP level
        IPv6 database, returns the ISP that provides connectivity for the
        address.
        """
        return geoip.isp_by_addr(self)

    @property
    def org(self):
        """
        If :func:`~lars.geoip.init_databases` has been called with an IPv6
        organisation level database, returns the name of the organisation the
        address belongs to.
        """
        return geoip.org_by_addr(self)

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
    # pylint: disable=too-many-ancestors
    """
    This type is returned by the :func:`network` function. This class
    represents and manipulates 32-bit IPv4 networks.

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
    pass


class IPv4Port(IPv4Address):
    # pylint: disable=too-many-ancestors
    """
    Represents an IPv4 address and port number.

    This type is returned by the :func:`address` function and represents an
    IPv4 address and port number. Other than this, all properties of the base
    :class:`IPv4Address` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
    """

    def __init__(self, address):
        # pylint: disable=redefined-outer-name
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
    # pylint: disable=too-many-ancestors
    """
    Represents an IPv6 address and port number.

    This type is returned by the :func:`address` function an represents an IPv6
    address and port number. The string representation of an IPv6 address with
    port necessarily wraps the address portion in square brakcets as otherwise
    the port number will make the address ambiguous. Other than this, all
    properties of the base :class:`IPv6Address` class are equivalent.

    .. attribute:: port

       An integer representing the network port for a connection
    """

    def __init__(self, address):
        # pylint: disable=redefined-outer-name,unused-variable
        addr, sep, port = address.rpartition(':')
        if port.endswith(']'):  # [IPv6addr]
            addr = '%s:%s' % (addr[1:], port[:-1])
            port = None
        elif addr.endswith(']'):  # [IPv6addr]:port
            addr = addr[1:-1]
            port = int(port)
            if not 0 <= port <= 65535:
                raise ValueError('Invalid port %d' % port)
        else:  # IPv6addr
            addr = '%s:%s' % (addr, port)
            port = None
        super(IPv6Port, self).__init__(addr)
        self.port = port

    def __str__(self):
        result = super(IPv6Port, self).__str__()
        if self.port is not None:
            return '[%s]:%d' % (result, self.port)
        return result


class IPv6Network(ipaddress.IPv6Network):
    # pylint: disable=too-many-ancestors
    """
    This type is returned by the :func:`network` function. This class
    represents and manipulates 128-bit IPv6 networks.

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
    pass
