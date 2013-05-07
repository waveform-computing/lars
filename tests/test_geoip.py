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
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import os
import gzip
import urlparse
import urllib2
import socket

import pygeoip
import pytest

from www2csv import geoip


slow = pytest.mark.slow

GEOLITE_COUNTRY_IPV4_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz'
GEOLITE_COUNTRY_IPV6_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoIPv6.dat.gz'
GEOLITE_CITY_IPV4_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz'
GEOLITE_CITY_IPV6_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLiteCityv6-beta/GeoLiteCityv6.dat.gz'
GEOLITE_COUNTRY_IPV4_FILE = 'country_v4.dat'
GEOLITE_COUNTRY_IPV6_FILE = 'country_v6.dat'
GEOLITE_CITY_IPV4_FILE = 'city_v4.dat'
GEOLITE_CITY_IPV6_FILE = 'city_v6.dat'


def copy(source, target):
    while True:
        data = source.read(65536)
        if not data:
            break
        target.write(data)

def download_gz(url, filename):
    if not os.path.exists(filename):
        if not os.path.exists(filename + '.gz'):
            with open(filename + '.gz', 'wb') as target:
                source = urllib2.urlopen(url)
                copy(source, target)
        with open(filename, 'wb') as target:
            with gzip.open(filename + '.gz') as source:
                copy(source, target)
        os.unlink(filename + '.gz')

@pytest.fixture
def geolite_country_ipv4_file():
    result = os.path.join(os.environ.get('TEMP', '/tmp'), GEOLITE_COUNTRY_IPV4_FILE)
    download_gz(GEOLITE_COUNTRY_IPV4_URL, result)
    return result

@pytest.fixture
def geolite_country_ipv6_file():
    result = os.path.join(os.environ.get('TEMP', '/tmp'), GEOLITE_COUNTRY_IPV6_FILE)
    download_gz(GEOLITE_COUNTRY_IPV6_URL, result)
    return result

@pytest.fixture
def geolite_city_ipv4_file():
    result = os.path.join(os.environ.get('TEMP', '/tmp'), GEOLITE_CITY_IPV4_FILE)
    download_gz(GEOLITE_CITY_IPV4_URL, result)
    return result

@pytest.fixture
def geolite_city_ipv6_file():
    result = os.path.join(os.environ.get('TEMP', '/tmp'), GEOLITE_CITY_IPV6_FILE)
    download_gz(GEOLITE_CITY_IPV6_URL, result)
    return result

def test_countries_v4(geolite_country_ipv4_file):
    geoip.init_database(geolite_country_ipv4_file)
    assert geoip.country_code_by_addr('127.0.0.1') is None
    assert geoip.country_code_by_addr_v6('::1') is None
    assert geoip.country_code_by_addr_v6('::1') is None
    # These are reasonably safe assumptions: the whole 8x block is assigned to
    # the Europe RIR (with 80 being used by UK ISPs only), and 9 is IBM
    assert geoip.country_code_by_addr('80.0.0.0') == 'GB'
    assert geoip.country_code_by_addr('9.0.0.0') == 'US'
    with pytest.raises(pygeoip.GeoIPError):
        geoip.region_by_addr('80.0.0.0')
    with pytest.raises(pygeoip.GeoIPError):
        geoip.city_by_addr('80.0.0.0')
    # XXX Hopefully python.org won't move from NL for a while...
    python_addr = socket.getaddrinfo('python.org', 0, socket.AF_INET, socket.SOCK_STREAM)[0][-1][0]
    assert geoip.country_code_by_addr(python_addr) == 'NL'

def test_countries_v6(geolite_country_ipv4_file, geolite_country_ipv6_file):
    geoip.init_database(geolite_country_ipv4_file, geolite_country_ipv6_file)
    # XXX Is there a better way of testing this with IPv6?
    python_addr = socket.getaddrinfo('python.org', 0, socket.AF_INET6, socket.SOCK_STREAM)[0][-1][0]
    assert geoip.country_code_by_addr_v6(python_addr) == 'NL'

def test_cities_v4(geolite_city_ipv4_file):
    geoip.init_database(geolite_city_ipv4_file)
    assert geoip.region_by_addr('127.0.0.1') is None
    assert geoip.region_by_addr('80.0.0.0') == 'D9'
    assert geoip.region_by_addr('9.0.0.0') == 'NC'
    assert geoip.city_by_addr('127.0.0.1') is None
    assert geoip.city_by_addr('80.0.0.0') == 'Greenford'
    assert geoip.city_by_addr('9.0.0.0' ) == 'Durham'
    assert geoip.coords_by_addr('80.0.0.0') == geoip.GeoCoord(-0.33330000000000837, 51.516699999999986)
    assert geoip.coords_by_addr('9.0.0.0') == geoip.GeoCoord(-78.8986, 35.994)
    python_addr = socket.getaddrinfo('python.org', 0, socket.AF_INET, socket.SOCK_STREAM)[0][-1][0]
    assert geoip.region_by_addr(python_addr) is None

@pytest.mark.xfail(reason='invalid database type 30')
def test_cities_v6(geolite_city_ipv4_file, geolite_city_ipv6_file):
    # XXX Can't test any of region, city or coord for v6 as the pygeoip
    # currently doesn't recognize the city-level IPv6 database as valid...
    geoip.init_database(geolite_city_ipv4_file, geolite_city_ipv6_file)
    python_addr = socket.getaddrinfo('python.org', 0, socket.AF_INET6, socket.SOCK_STREAM)[0][-1][0]
    assert geoip.region_by_addr_v6(python_v6_addr) is None
