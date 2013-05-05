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
Provides a common interface to the GeoIP database.

This module wraps the official GeoIP API or the pygeoip API to provide a common
set of calls for the datatypes module (specifically the IPv6Port and IPv4Port
classes' calculated properties). In the case that neither of these packages are
available, stubs are created which simply raise NotImplementedError in the case
that they are called.

The official bindings (which rely on a compiled library) are rather faster than
the pure-Python pygeoip package, but being compiled they can be tricky to
install on certain platforms, and thus this module aims to make working with
the simpler pygeoip API as seamless as possible.

Reference
=========

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from collections import namedtuple

pygeoip = None
GeoIP = None
try:
    import GeoIP
except ImportError:
    import pygeoip


_GEOIP_DATABASE = None


GeoCoord = namedtuple('GeoCoord', ('longitude', 'latitude'))


if GeoIP:
    def init_database(filename, memcache=True):
        """
        Initializes the global GeoIP database instance in a thread-safe manner.

        If the GeoIP country database hasn't been opened, this function will
        open it, and store a global reference to it. By default, the function
        will cache all data in memory (on the assumption that just about any
        server has more than sufficient RAM for this these days), but this
        behaviour can be overridden with the ``memcache`` parameter.

        :param str filename: The filename of the database
        :param bool memcache: Set to False if you don't wish to cache the db in RAM
        """
        global _GEOIP_DATABASE
        if _GEOIP_DATABASE:
            raise ValueError('GeoIP database has already been initialized')
        _GEOIP_DATABASE = GeoIP.open(filename, GeoIP.GEOIP_MEMORY_CACHE if memcache else 0)

    def country_code_by_addr(address):
        """
        Returns the country code associated with the specified address.

        :param str address: The address to lookup the country for
        :returns str: The country code associated with the address, or None
        """
        return _GEOIP_DATABASE.country_code_by_addr(address)

    def country_code_by_addr_v6(address):
        """
        Returns the country code associated with the specified address.

        :param str address: The address to lookup the country for
        :returns str: The country code associated with the address, or None
        """
        return _GEOIP_DATABASE.country_code_by_addr_v6(address)

    def region_by_addr(address):
        """
        Returns the region (e.g. state) associated with the address.

        Given an address, this function returns the region associated with it.
        In the case of the US, this is the state. In the case of other
        countries it may be a state, county, something GeoIP-specific or simply
        undefined. Note: this function will raise an exception if the GeoIP
        database loaded is country-level only.

        :param str address: The address to lookup the region for
        :returns str: The region associated with the address, or None
        """
        # The region_by_addr function in the official GeoIP API bindings just
        # dumps core (in both the Ubuntu packaged version and a build of the
        # latest ones), so we use record_by_addr here instead and hope we've
        # got a city-level database
        rec == _GEOIP_DATABASE.record_by_addr(address)
        if rec:
            return rec.get('region_name')

    def region_by_addr_v6(address):
        """
        Returns the region (e.g. state) associated with the address.

        Given an address, this function returns the region associated with it.
        In the case of the US, this is the state. In the case of other
        countries it may be a state, county, something GeoIP-specific or simply
        undefined. Note: this function will raise an exception if the GeoIP
        database loaded is country-level only.

        :param str address: The address to lookup the region for
        :returns str: The region associated with the address, or None
        """
        # See region_by_addr above
        rec == _GEOIP_DATABASE.record_by_addr_v6(address)
        if rec:
            return rec.get('region_name')

    def city_by_addr(address):
        """
        Returns the city associated with the address.

        Given an address, this function returns the city associated with it.
        Note: this function will raise an exception if the GeoIP database
        loaded is above city level.

        :param str address: The address to lookup the city for
        :returns str: The city associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr(address)
        if rec:
            return rec.get('city')

    def city_by_addr_v6(address):
        """
        Returns the city associated with the address.

        Given an address, this function returns the city associated with it.
        Note: this function will raise an exception if the GeoIP database
        loaded is above city level.

        :param str address: The address to lookup the city for
        :returns str: The city associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr_v6(address)
        if rec:
            return rec.get('city')

    def coord_by_addr(address):
        """
        Returns the coordinates (long, lat) associated with the address.

        Given an address, this function returns a tuple with the attributes
        longitude and latitude (in that order) representing the (very)
        approximate coordinates of the address on the globe.  Note: this
        function will raise an exception if the GeoIP database loaded is above
        city level.

        :param str address: The address to locate
        :returns str: The coordinates associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr(address)
        if rec:
            return GeoCoord(rec['longitude'], rec['latitude'])

    def coord_by_addr_v6(address):
        """
        Returns the coordinates (long, lat) associated with the address.

        Given an address, this function returns a tuple with the attributes
        longitude and latitude (in that order) representing the (very)
        approximate coordinates of the address on the globe.  Note: this
        function will raise an exception if the GeoIP database loaded is above
        city level.

        :param str address: The address to locate
        :returns str: The coordinates associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr_v6(address)
        if rec:
            return GeoCoord(rec['longitude'], rec['latitude'])


elif pygeoip:
    def init_database(filename, memcache=True):
        """
        Initializes the global GeoIP database instance in a thread-safe manner.

        If the GeoIP country database hasn't been opened, this function will
        open it, and store a global reference to it. By default, the function
        will cache all data in memory (on the assumption that just about any
        server has more than sufficient RAM for this these days), but this
        behaviour can be overridden with the ``memcache`` parameter.

        :param str filename: The filename of the database
        :param bool memcache: Set to False if you don't wish to cache the db in RAM
        """
        global _GEOIP_DATABASE
        if _GEOIP_DATABASE:
            raise ValueError('GeoIP database has already been initialized')
        _GEOIP_DATABASE = pygeoip.GeoIP(filename, pygeoip.MEMORY_CACHE if memcache else 0)

    def country_code_by_addr(address):
        """
        Returns the country code associated with the specified address.

        :param str address: The address to lookup the country for
        :returns str: The country code associated with the address, or None
        """
        # pygeoip returns '' instead of None in case a match isn't found. For
        # consistency with the GeoIP API, we convert this to None
        return _GEOIP_DATABASE.country_code_by_addr(address) or None

    def region_by_addr(address):
        """
        Returns the region (e.g. state) associated with the address.

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
        return _GEOIP_DATABASE.region_by_addr(address).get('region_name') or None

    def city_by_addr(address):
        """
        Returns the city associated with the address.

        Given an address, this function returns the city associated with it.
        Note: this function will raise an exception if the GeoIP database
        loaded is above city level.

        :param str address: The address to lookup the city for
        :returns str: The city associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr(address)
        if rec:
            return rec.get('city')

    def coord_by_addr(address):
        """
        Returns the coordinates (long, lat) associated with the address.

        Given an address, this function returns a tuple with the attributes
        longitude and latitude (in that order) representing the (very)
        approximate coordinates of the address on the globe.  Note: this
        function will raise an exception if the GeoIP database loaded is above
        city level.

        :param str address: The address to locate
        :returns str: The coordinates associated with the address, or None
        """
        rec == _GEOIP_DATABASE.record_by_addr(address)
        if rec:
            return GeoCoord(rec['longitude'], rec['latitude'])

    country_code_by_addr_v6 = country_code_by_addr
    region_by_addr_v6 = region_by_addr
    city_by_addr_v6 = city_by_addr
    coord_by_addr_v6 = coord_by_addr


else:
    def init_database(*args, **kwargs):
        raise NotImplementedError(
            'You must install the official GeoIP Python bindings or the '
            'pygeoip package from PyPI')

    country_by_addr = init_database
    country_by_addr_v6 = init_database
    region_by_addr = init_database
    region_by_addr_v6 = init_database
    city_by_addr = init_database
    city_by_addr_v6 = init_database
    coord_by_addr = init_database
    coord_by_addr_v6 = init_database
