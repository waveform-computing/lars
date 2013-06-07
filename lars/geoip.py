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

.. autofunction:: init_database

.. autofunction:: country_code_by_addr

.. autofunction:: country_code_by_addr_v6

.. autofunction:: city_by_addr

.. autofunction:: city_by_addr_v6

.. autofunction:: region_by_addr

.. autofunction:: region_by_addr_v6

.. autofunction:: coords_by_addr

.. autofunction:: coords_by_addr_v6


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

import pygeoip


_GEOIP_IPV4_DATABASE = None
_GEOIP_IPV6_DATABASE = None


GeoCoord = namedtuple('GeoCoord', ('longitude', 'latitude'))


def init_database(v4_filename, v6_filename=None, memcache=True):
    """
    Initializes the global GeoIP database instance in a thread-safe manner.

    This function opens GeoIP databases for use by the
    :class:`~lars.datatypes.IPv4Address` and
    :class:`~lars.datatypes.IPv6Address` classes. GeoIP databases are
    hierarchical: if you open a country-only database, you will only be able to
    use country-level lookups. However, city-level databases enable all
    supported lookups (country, region, city, and coordinates).

    By default, the function caches the entire content of (both) the
    database(s) in memory (on the assumption that just about any machine has
    more than sufficient RAM for this), but this behaviour can be overridden
    with the *memcache* parameter.

    The optional *v6_filename* parameter specifies the location of the
    IPv6 database which will be used for IPv6 addresses. The GeoIP IPv6
    databases are orthogonal to the IPv4 databases (you cannot lookup IPv4
    addresses using an IPv6 database) - hence why the two databases are
    stored and specified separately.

    .. warning::

        At the time of writing, the free GeoLite IPv6 city-level database does
        not work (the authors seem to be using a new database format which the
        pygeoip API does not yet know). This does not affect the IPv4
        city-level database.

    :param str v4_filename: The filename of the IPv4 database
    :param str v6_filename: The filename of the IPv6 database (optional)
    :param bool memcache: Set to False if you don't wish to cache the db in RAM (optional)
    """
    global _GEOIP_IPV4_DATABASE
    global _GEOIP_IPV6_DATABASE
    _GEOIP_IPV4_DATABASE = pygeoip.GeoIP(
        v4_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    if v6_filename:
        _GEOIP_IPV6_DATABASE = pygeoip.GeoIP(
            v6_filename, pygeoip.MEMORY_CACHE if memcache else 0)
    else:
        _GEOIP_IPV6_DATABASE = None

def country_code_by_addr(address):
    """
    Returns the country code associated with the specified address. You should
    use the :attr:`~lars.datatypes.IPv4Address.country` attribute instead of
    this function.

    :param str address: The address to lookup the country for
    :returns str: The country code associated with the address, or None
    """
    # pygeoip returns '' instead of None in case a match isn't found. For
    # consistency with the GeoIP API, we convert this to None
    return _GEOIP_IPV4_DATABASE.country_code_by_addr(address) or None

def country_code_by_addr_v6(address):
    """
    Returns the country code associated with the specified address. You should
    use the :attr:`~lars.datatypes.IPv6Address.country` attribute instead of
    this function.

    :param str address: The address to lookup the country for
    :returns str: The country code associated with the address, or None
    """
    # pygeoip returns '' instead of None in case a match isn't found. For
    # consistency with the GeoIP API, we convert this to None
    if _GEOIP_IPV6_DATABASE:
        return _GEOIP_IPV6_DATABASE.country_code_by_addr(address) or None

def region_by_addr(address):
    """
    Returns the region (e.g. state) associated with the address. You should
    use the :attr:`~lars.datatypes.IPv4Address.region` attribute instead of
    this function.

    Given an address, this function returns the region associated with it.
    In the case of the US, this is the state. In the case of other
    countries it may be a state, county, something GeoIP-specific or simply
    undefined. Note: this function will raise an exception if the GeoIP
    database loaded is country-level only.

    :param str address: The address to lookup the region for
    :returns str: The region associated with the address, or None
    """
    # This is safe as pygeoip returns a dictionary with blank values in the
    # case of no match
    return _GEOIP_IPV4_DATABASE.region_by_addr(address).get('region_name') or None

def region_by_addr_v6(address):
    """
    Returns the region (e.g. state) associated with the address. You should use
    the :attr:`~lars.datatypes.IPv6Address.region` attribute instead of this
    function.

    Given an address, this function returns the region associated with it.
    In the case of the US, this is the state. In the case of other
    countries it may be a state, county, something GeoIP-specific or simply
    undefined. Note: this function will raise an exception if the GeoIP
    database loaded is country-level only.

    :param str address: The address to lookup the region for
    :returns str: The region associated with the address, or None
    """
    # This is safe as pygeoip returns a dictionary with blank values in the
    # case of no match
    if _GEOIP_IPV6_DATABASE:
        return _GEOIP_IPV6_DATABASE.region_by_addr(address).get('region_name') or None

def city_by_addr(address):
    """
    Returns the city associated with the address. You should use the
    :attr:`~lars.datatypes.IPv4Address.city` attribute instead of this
    function.

    Given an address, this function returns the city associated with it.
    Note: this function will raise an exception if the GeoIP database
    loaded is above city level.

    :param str address: The address to lookup the city for
    :returns str: The city associated with the address, or None
    """
    rec = _GEOIP_IPV4_DATABASE.record_by_addr(address)
    if rec:
        return rec.get('city')

def city_by_addr_v6(address):
    """
    Returns the city associated with the address. You should use the
    :attr:`~lars.datatypes.IPv6Address.city` attribute instead of this
    function.

    Given an address, this function returns the city associated with it.
    Note: this function will raise an exception if the GeoIP database
    loaded is above city level.

    :param str address: The address to lookup the city for
    :returns str: The city associated with the address, or None
    """
    if _GEOIP_IPV6_DATABASE:
        rec = _GEOIP_IPV6_DATABASE.record_by_addr(address)
        if rec:
            return rec.get('city')

def coords_by_addr(address):
    """
    Returns the coordinates (long, lat) associated with the address. You should
    use the :attr:`~lars.datatypes.IPv4Address.coords` attribute instead of
    this function.

    Given an address, this function returns a tuple with the attributes
    longitude and latitude (in that order) representing the (very)
    approximate coordinates of the address on the globe.  Note: this
    function will raise an exception if the GeoIP database loaded is above
    city level.

    :param str address: The address to locate
    :returns str: The coordinates associated with the address, or None
    """
    rec = _GEOIP_IPV4_DATABASE.record_by_addr(address)
    if rec:
        return GeoCoord(rec['longitude'], rec['latitude'])

def coords_by_addr_v6(address):
    """
    Returns the coordinates (long, lat) associated with the address. You should
    use the :attr:`~lars.datatypes.IPv6Address.coords` attribute instead of
    this function.

    Given an address, this function returns a tuple with the attributes
    longitude and latitude (in that order) representing the (very)
    approximate coordinates of the address on the globe.  Note: this
    function will raise an exception if the GeoIP database loaded is above
    city level.

    :param str address: The address to locate
    :returns str: The coordinates associated with the address, or None
    """
    if _GEOIP_IPV6_DATABASE:
        rec = _GEOIP_IPV6_DATABASE.record_by_addr(address)
        if rec:
            return GeoCoord(rec['longitude'], rec['latitude'])

