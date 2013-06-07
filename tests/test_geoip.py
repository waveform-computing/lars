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
import mock

from lars import geoip


def test_init_db():
    with mock.patch('tests.test_geoip.geoip.pygeoip.GeoIP') as mock_class:
        geoip.init_database('mock.dat')
        assert mock_class.called_with('mock.dat', pygeoip.MEMORY_CACHE)
        # Ensure when the IPv6 database isn't initialized we still get back
        # None, not errors (as the IPv6 database is optional)
        assert geoip._GEOIP_IPV6_DATABASE is None
        assert geoip.country_code_by_addr_v6('::1') is None
        assert geoip.region_by_addr_v6('::1') is None
        assert geoip.city_by_addr_v6('::1') is None
        assert geoip.coords_by_addr_v6('::1') is None
        mock_class.reset_mock()
        geoip.init_database('mock_v4.dat', 'mock_v6.dat', memcache=False)
        assert mock_class.call_count == 2
        assert mock_class.mock_calls == [
            mock.call('mock_v4.dat', 0),
            mock.call('mock_v6.dat', 0),
            ]

def test_countries_v4():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_DATABASE') as mock_db:
        geoip.country_code_by_addr('127.0.0.1')
        assert mock_db.country_code_by_addr.called_with('127.0.0.1')

def test_countries_v6():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_DATABASE') as mock_db:
        geoip.country_code_by_addr_v6('::1')
        assert mock_db.country_code_by_addr_v6.called_with('::1')

def test_cities_v4():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV4_DATABASE') as mock_db:
        geoip.region_by_addr('127.0.0.1')
        assert mock_db.region_by_addr.called_with('127.0.0.1')
        geoip.city_by_addr('127.0.0.1')
        assert mock_db.city_by_addr.called_with('127.0.0.1')
        geoip.coords_by_addr('127.0.0.1')
        assert mock_db.rec_by_addr.called_with('127.0.0.1')

def test_cities_v6():
    with mock.patch('tests.test_geoip.geoip._GEOIP_IPV6_DATABASE') as mock_db:
        geoip.region_by_addr('::1')
        assert mock_db.region_by_addr.called_with('::1')
        geoip.city_by_addr('::1')
        assert mock_db.city_by_addr.called_with('::1')
        geoip.coords_by_addr('::1')
        assert mock_db.rec_by_addr.called_with('::1')

