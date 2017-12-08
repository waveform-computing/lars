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

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import os
import gzip
import socket
try:
    from ipaddress import IPv4Address, IPv6Address
except ImportError:
    from ipaddr import IPv4Address, IPv6Address

import pygeoip
import pytest
import mock

from lars import geoip


def test_init_db():
    with mock.patch('tests.test_geoip.geoip.pygeoip.GeoIP') as mock_class:
        geoip.init_databases('mock.dat')
        assert mock_class.called_with('mock.dat', pygeoip.MEMORY_CACHE)
        # Ensure when the IPv6 database isn't initialized we get value errors
        # when requesting geoip info on IPv6 addresses
        # None, not errors (as the IPv6 database is optional)
        assert geoip._GEOIP_IPV6_GEO is None
        assert geoip._GEOIP_IPV4_ISP is None
        assert geoip._GEOIP_IPV6_ISP is None
        assert geoip._GEOIP_IPV4_ORG is None
        assert geoip._GEOIP_IPV6_ORG is None
        with pytest.raises(ValueError):
            geoip.country_code_by_addr(IPv6Address('::1'))
        with pytest.raises(ValueError):
            geoip.region_by_addr(IPv6Address('::1'))
        with pytest.raises(ValueError):
            geoip.city_by_addr(IPv6Address('::1'))
        with pytest.raises(ValueError):
            geoip.coords_by_addr(IPv6Address('::1'))
        with pytest.raises(ValueError):
            geoip.isp_by_addr(IPv4Address('127.0.0.1'))
        with pytest.raises(ValueError):
            geoip.org_by_addr(IPv4Address('127.0.0.1'))
        # Test loading no databases
        with pytest.raises(ValueError):
            geoip.init_databases()
        # Test loading every other database
        mock_class.reset_mock()
        geoip.init_databases(
                None, 'isp_v4.dat', 'org_v4.dat',
                'geo_v6.dat', 'isp_v6.dat', 'org_v6.dat',
                memcache=False)
        assert mock_class.call_count == 5
        assert mock_class.mock_calls == [
            mock.call('isp_v4.dat', 0),
            mock.call('org_v4.dat', 0),
            mock.call('geo_v6.dat', 0),
            mock.call('isp_v6.dat', 0),
            mock.call('org_v6.dat', 0),
            ]

def test_countries():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_GEO') as mock_db:
        geoip.country_code_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.country_code_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_GEO') as mock_db:
        geoip.country_code_by_addr(IPv6Address('::1'))
        assert mock_db.country_code_by_addr.called_with('::1')

def test_regions():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_GEO') as mock_db:
        geoip.region_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.record_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_GEO') as mock_db:
        geoip.region_by_addr(IPv6Address('::1'))
        assert mock_db.record_by_addr.called_with('::1')

def test_cities():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_GEO') as mock_db:
        geoip.region_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.region_by_addr.called_with('127.0.0.1')
        geoip.city_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.city_by_addr.called_with('127.0.0.1')
        geoip.coords_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.rec_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_GEO') as mock_db:
        geoip.region_by_addr(IPv6Address('::1'))
        assert mock_db.region_by_addr.called_with('::1')
        geoip.city_by_addr(IPv6Address('::1'))
        assert mock_db.city_by_addr.called_with('::1')
        geoip.coords_by_addr(IPv6Address('::1'))
        assert mock_db.rec_by_addr.called_with('::1')

def test_coords():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_GEO') as mock_db:
        geoip.coords_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.record_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_GEO') as mock_db:
        geoip.coords_by_addr(IPv6Address('::1'))
        assert mock_db.record_by_addr.called_with('::1')

def test_isp():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_ISP') as mock_db:
        geoip.isp_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.org_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_ISP') as mock_db:
        geoip.isp_by_addr(IPv6Address('::1'))
        assert mock_db.org_by_addr.called_with('::1')

def test_org():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_ORG') as mock_db:
        geoip.org_by_addr(IPv4Address('127.0.0.1'))
        assert mock_db.org_by_addr.called_with('127.0.0.1')
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_ORG') as mock_db:
        geoip.org_by_addr(IPv6Address('::1'))
        assert mock_db.org_by_addr.called_with('::1')

