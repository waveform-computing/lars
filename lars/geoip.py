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

"""
This module provides a common interface to the GeoIP database. Most users will
only need to be aware of the :func:`init_database` function in this module,
which is used to initialize the GeoIP database(s). All other functions should
be ignored; instead, users should use the
:attr:`~lars.datatypes.IPv4Address.country`,
:attr:`~lars.datatypes.IPv4Address.region`,
:attr:`~lars.datatypes.IPv4Address.city`, and
:attr:`~lars.datatypes.IPv4Address.coords` attributes of the
:class:`~lars.datatypes.IPv4Address` and
:class:`~lars.datatypes.IPv6Address` classes.


Functions
=========

.. autofunction:: init_databases

.. autofunction:: country_code_by_addr

.. autofunction:: city_by_addr

.. autofunction:: region_by_addr

.. autofunction:: coords_by_addr

.. autofunction:: isp_by_addr

.. autofunction:: org_by_addr


Examples
========

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from collections import namedtuple
try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress

import pygeoip

str = type('')  # pylint: disable=redefined-builtin,invalid-name


_MAXMIND_ENCODING = 'latin1'
_GEOIP_IPV4_GEO = None
_GEOIP_IPV4_ISP = None
_GEOIP_IPV4_ORG = None
_GEOIP_IPV6_GEO = None
_GEOIP_IPV6_ISP = None
_GEOIP_IPV6_ORG = None


GeoCoord = namedtuple('GeoCoord', ('longitude', 'latitude'))


def init_databases(
        v4_geo_filename=None, v4_isp_filename=None, v4_org_filename=None,
        v6_geo_filename=None, v6_isp_filename=None, v6_org_filename=None,
        memcache=True):
    # pylint: disable=too-many-arguments,global-statement
    """
    Initializes the global GeoIP database instances in a thread-safe manner.

    This function opens GeoIP databases for use by the
    :class:`~lars.datatypes.IPv4Address` and
    :class:`~lars.datatypes.IPv6Address` classes. There are several types of
    GeoIP databases. The country, region, and city databases are considered
    "geographical" databases and should be specified for the *v4_geo_filename*
    and/or *v6_geo_filename* databases (for IPv4 and IPv6 databases
    respectively). The ISP and organisational databases are treated separately
    as they contain no geographical information. If you have such databases,
    specify them as the values of the *v4_isp_filename*, *v6_isp_filename*,
    *v4_org_filename*, and *v6_org_filename* parameters (all optional).

    GeoIP geographical databases are hierarchical: if you open a country
    database, you will only be able to use country-level lookups. However,
    city-level databases enable all geographical lookups (country, region,
    city, and coordinates).

    By default, the function caches the entire content of database(s) in memory
    (on the assumption that just about any modern machine has more than
    sufficient RAM for this), but this behaviour can be overridden with the
    *memcache* parameter.

    .. warning::

        At the time of writing, the free GeoLite IPv6 city-level database does
        not work (the authors seem to be using a new database format which the
        pygeoip API does not yet know). This does not affect the IPv4
        city-level database.

    :param str v4_geo_filename:
        The filename of the IPv4 geographic database (optional)

    :param str v4_isp_filename:
        The filename of the IPv4 ISP database (optional)

    :param str v4_org_filename:
        The filename of the IPv4 organisation database (optional)

    :param str v6_geo_filename:
        The filename of the IPv6 geographic database (optional)

    :param str v6_isp_filename:
        The filename of the IPv6 ISP database (optional)

    :param str v6_org_filename:
        The filename of the IPv6 organisation database (optional)

    :param bool memcache:
        Set to False if you don't wish to cache the db in RAM (optional)
    """
    global \
        _GEOIP_IPV4_GEO, _GEOIP_IPV4_ISP, _GEOIP_IPV4_ORG, \
        _GEOIP_IPV6_GEO, _GEOIP_IPV6_ISP, _GEOIP_IPV6_ORG
    if not (
            v4_geo_filename or
            v4_isp_filename or
            v4_org_filename or
            v6_geo_filename or
            v6_isp_filename or
            v6_org_filename):
        raise ValueError('You must call init_database with a database to load')
    if v4_geo_filename:
        _GEOIP_IPV4_GEO = pygeoip.GeoIP(
            v4_geo_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v4_isp_filename:
        _GEOIP_IPV4_ISP = pygeoip.GeoIP(
            v4_isp_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v4_org_filename:
        _GEOIP_IPV4_ORG = pygeoip.GeoIP(
            v4_org_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v6_geo_filename:
        _GEOIP_IPV6_GEO = pygeoip.GeoIP(
            v6_geo_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v6_isp_filename:
        _GEOIP_IPV6_ISP = pygeoip.GeoIP(
            v6_isp_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v6_org_filename:
        _GEOIP_IPV6_ORG = pygeoip.GeoIP(
            v6_org_filename, pygeoip.MEMORY_CACHE if memcache else 0)


def country_code_by_addr(address):
    """
    Returns the country code associated with the specified address, or None if
    the address is not found in the GeoIP geographical database. You should
    use the :attr:`~lars.datatypes.IPv4Address.country` or
    :attr:`~lars.datatypes.IPv6Address.country` attributes instead of this
    function.

    If the geographical database for the address type has not been initialized,
    the function raises a ValueError.

    :param address: The address to lookup the country for
    :returns str: The country code associated with the address
    """
    # pygeoip returns '' instead of None in case a match isn't found. For
    # consistency with the GeoIP API, we convert this to None
    try:
        if isinstance(address, ipaddress.IPv4Address):
            result = _GEOIP_IPV4_GEO.country_code_by_addr(address.compressed)
        else:
            result = _GEOIP_IPV6_GEO.country_code_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized geo database while looking up country '
            'for address %s' % address)
    else:
        if isinstance(result, str):
            return result
        return result.decode(_MAXMIND_ENCODING)


def region_by_addr(address):
    """
    Returns the region (e.g. state) associated with the address. You should use
    the :attr:`~lars.datatypes.IPv4Address.region` or
    :attr:`~lars.datatypes.IPv6Address.region` attributes instead of this
    function.

    Given an address, this function returns the region associated with it.
    In the case of the US, this is the state. In the case of other
    countries it may be a state, county, something GeoIP-specific or simply
    undefined. Note: this function will raise an exception if the GeoIP
    database loaded is country-level only.

    If the geographical database for the address type has not been initialized,
    the function raises a ValueError.

    :param address: The address to lookup the region for
    :returns str: The region associated with the address, or None
    """
    # This is safe as pygeoip returns a dictionary with blank values in the
    # case of no match
    try:
        if isinstance(address, ipaddress.IPv4Address):
            rec = _GEOIP_IPV4_GEO.region_by_addr(address.compressed)
        else:
            rec = _GEOIP_IPV6_GEO.region_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized geo database while looking up country '
            'for address %s' % address)
    if rec and 'region_name' in rec:
        result = rec['region_name']
        if isinstance(result, str):
            return result
        return result.decode(_MAXMIND_ENCODING)


def city_by_addr(address):
    """
    Returns the city associated with the address. You should use the
    :attr:`~lars.datatypes.IPv4Address.city` or
    :attr:`~lars.datatypes.IPv6Address.city` attributes instead of this
    function.

    Given an address, this function returns the city associated with it.
    Note: this function will raise an exception if the GeoIP database
    loaded is above city level.

    If the geographical database for the address type has not been initialized,
    the function raises a ValueError.

    :param address: The address to lookup the city for
    :returns str: The city associated with the address, or None
    """
    try:
        if isinstance(address, ipaddress.IPv4Address):
            rec = _GEOIP_IPV4_GEO.record_by_addr(address.compressed)
        else:
            rec = _GEOIP_IPV6_GEO.record_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized geo database while looking up country '
            'for address %s' % address)
    if rec and 'city' in rec:
        result = rec['city']
        if isinstance(result, str):
            return result
        return result.decode(_MAXMIND_ENCODING)


def coords_by_addr(address):
    """
    Returns the coordinates (long, lat) associated with the address. You should
    use the :attr:`~lars.datatypes.IPv4Address.coords` or
    :attr:`~lars.datatypes.IPv4Address.coords` attributes instead of this
    function.

    Given an address, this function returns a tuple with the attributes
    longitude and latitude (in that order) representing the (very)
    approximate coordinates of the address on the globe.  Note: this
    function will raise an exception if the GeoIP database loaded is above
    city level.

    If the geographical database for the address type has not been initialized,
    the function raises a ValueError.

    :param address: The address to locate
    :returns str: The coordinates associated with the address, or None
    """
    try:
        if isinstance(address, ipaddress.IPv4Address):
            rec = _GEOIP_IPV4_GEO.record_by_addr(address.compressed)
        else:
            rec = _GEOIP_IPV6_GEO.record_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized geo database while looking up country '
            'for address %s' % address)
    if rec:
        return GeoCoord(rec['longitude'], rec['latitude'])


def isp_by_addr(address):
    """
    Returns the ISP that services the address. You should use the
    :attr:`~lars.datatypes.IPv4Address.isp` or
    :attr:`~lars.datatypes.IPv4Address.isp` attributes instead of this
    function.

    If the ISP database for the address type has not been initialized, the
    function raises a ValueError.

    :param address: The address to lookup the ISP for
    :returns str: The ISP associated with the address, or None
    """
    try:
        if isinstance(address, ipaddress.IPv4Address):
            result = _GEOIP_IPV4_ISP.org_by_addr(address.compressed)
        else:
            result = _GEOIP_IPV6_ISP.org_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized ISP database while looking up ISP '
            'for address %s' % address)
    else:
        if isinstance(result, str):
            return result
        return result.decode(_MAXMIND_ENCODING)


def org_by_addr(address):
    """
    Returns the organisation that owns the address, or the ISP that services
    the address (in the case that the organisation has opted not to reveal its
    address). If the organisational database for the address type has not been
    initialized, the function raises a ValueError.
    """
    try:
        if isinstance(address, ipaddress.IPv4Address):
            result = _GEOIP_IPV4_ORG.org_by_addr(address.compressed)
        else:
            result = _GEOIP_IPV6_ORG.org_by_addr(address.compressed)
    except AttributeError:
        raise ValueError(
            'Uninitialized organisation database while looking up org '
            'for address %s' % address)
    else:
        if isinstance(result, str):
            return result
        return result.decode(_MAXMIND_ENCODING)
