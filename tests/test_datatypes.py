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

import sys
import os
import shutil
import sqlite3
from datetime import datetime, date, time
try:
    from ipaddress import IPv4Address, IPv6Address
except ImportError:
    from ipaddr import IPv4Address, IPv6Address

import pytest
import mock

from lars import datatypes as dt, geoip


INTRANET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-05-02 17:42:15
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status cs(User-Agent)
2002-05-02 17:42:15 172.22.255.255 - 172.30.255.255 80 GET /images/picture.jpg - 200 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server)
"""

INTERNET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-05-24 20:18:01
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

FTP_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-06-04 16:40:23
#Fields: time c-ip cs-method cs-uri-stem sc-status 
16:40:23 10.152.10.200 [6994]USER anonymous 331
16:40:25 10.152.10.200 [6994]PASS anonymous@example.net 530
"""


def test_sanitize_name():
    assert dt.sanitize_name('foo') == 'foo'
    assert dt.sanitize_name('FOO') == 'FOO'
    assert dt.sanitize_name(' foo ') == '_foo_'
    assert dt.sanitize_name('rs-date') == 'rs_date'
    assert dt.sanitize_name('cs(User-Agent)') == 'cs_User_Agent_'
    with pytest.raises(ValueError):
        dt.sanitize_name('')

def test_path():
    assert dt.path('/') == dt.Path('/', '', '')
    assert dt.path('/bin') == dt.Path('/', 'bin', '')
    assert dt.path('/foo/bar') == dt.Path('/foo', 'bar', '')
    assert dt.path('/foo/bar').basename_no_ext == 'bar'
    assert dt.path('/foo/bar.baz') == dt.Path('/foo', 'bar.baz', '.baz')
    assert dt.path('/foo/bar.baz').basename_no_ext == 'bar'
    assert dt.path('/foo/.baz').basename == '.baz'
    assert dt.path('/foo/.baz').ext == ''
    assert dt.path('/foo/bar').dirname == '/foo'
    assert dt.path('//foo/bar').dirname == '//foo'
    assert dt.path('/').dirname == '/'
    assert dt.path('/').basename == ''
    assert dt.path('//').dirname == '//'
    assert dt.path('/foo//').dirname == '/foo'
    assert dt.path('/').isabs
    assert dt.path('/foo/bar').isabs
    assert not dt.path('foo/bar').isabs
    assert dt.path('/foo/bar/baz/quux').dirs == ['foo', 'bar', 'baz']
    assert dt.path('/foo/bar/baz/').dirs == ['foo', 'bar', 'baz']
    assert dt.path('/foo/bar/baz').dirs == ['foo', 'bar']
    assert dt.path('/').dirs == []
    assert dt.path('/foo/bar').join('baz') == dt.path('/foo/bar/baz')
    assert dt.path('/foo/bar').join('baz', 'quux') == dt.path('/foo/bar/baz/quux')
    assert dt.path('/').join('baz') == dt.path('/baz')
    assert dt.path('/foo').join(dt.path('bar/baz')) == dt.path('/foo/bar/baz')
    assert dt.path('/foo').join('/bar/baz') == dt.path('/bar/baz')
    assert dt.path('foo').join('/bar/baz') == dt.path('/bar/baz')

def test_url():
    assert dt.url('foo') == dt.Url('', '', 'foo', '', '', '')
    assert dt.url('//foo/bar') == dt.Url('', 'foo', '/bar', '', '', '')
    assert dt.url('http://foo/') == dt.Url('http', 'foo', '/', '', '', '')
    assert dt.url('http://foo/bar?baz=quux') == dt.Url('http', 'foo', '/bar', '', 'baz=quux', '')
    assert dt.url('https://foo/bar#baz') == dt.Url('https', 'foo', '/bar', '', '', 'baz')
    u = dt.url('http://localhost/foo/bar#baz')
    assert u.scheme == 'http'
    assert u.netloc == 'localhost'
    assert u.path == dt.Path('/foo', 'bar', '')
    assert u.path_str == '/foo/bar'
    assert u.fragment == 'baz'
    assert u.username is None
    assert u.password is None
    assert u.port is None
    assert u.hostname == dt.hostname('localhost')
    assert u.hostname.address == dt.address('127.0.0.1')

def test_url_query():
    url = dt.url('http://foo/bar?baz=quux&x=1&y=')
    assert 'baz' in url.query
    assert 'x' in url.query
    assert 'y' in url.query
    assert not 'z' in url.query
    assert url.query['baz'] == ['quux']
    assert url.query['x'] == ['1']
    assert url.query['y'] == ['']

def test_request():
    assert dt.request('OPTIONS * HTTP/1.1') == dt.Request('OPTIONS', None, 'HTTP/1.1')
    assert dt.request('GET / HTTP/1.0') == dt.Request('GET', dt.url('/'), 'HTTP/1.0')
    assert dt.request('POST /foo/bar/baz?query HTTP/1.0') == dt.Request('POST', dt.url('/foo/bar/baz?query'), 'HTTP/1.0')
    with pytest.raises(ValueError):
        assert dt.request('')
    with pytest.raises(ValueError):
        assert dt.request('GET')
    with pytest.raises(ValueError):
        assert dt.request('GET  HTTP/1.0')
    with pytest.raises(ValueError):
        assert dt.request('GET /foo/bar')

def test_row():
    NewRow = dt.row('foo', 'bar', 'baz')
    assert NewRow._fields == ('foo', 'bar', 'baz')
    assert NewRow(1, 2, 3) == (1, 2, 3)
    assert NewRow(1, 2, 3).foo == 1
    assert NewRow(1, 2, 3).bar == 2
    assert NewRow(1, 2, 3).baz == 3

def test_datetime():
    assert dt.datetime('2000-01-01 12:34:56') == datetime(2000, 1, 1, 12, 34, 56)
    assert dt.datetime('1986-02-28 00:00:00') == datetime(1986, 2, 28)
    with pytest.raises(ValueError):
        dt.datetime('2000-01-32 12:34:56')
    with pytest.raises(ValueError):
        dt.datetime('2000-01-30 12:34:56 PM')
    with pytest.raises(ValueError):
        dt.datetime('foo')

def test_date():
    assert dt.date('2000-01-01') == date(2000, 1, 1)
    assert dt.date('1986-02-28') == date(1986, 2, 28)
    with pytest.raises(ValueError):
        dt.date('1 Jan 2001')
    with pytest.raises(ValueError):
        dt.date('2000-01-32')
    with pytest.raises(ValueError):
        dt.date('abc')

def test_time():
    assert dt.time('12:34:56') == time(12, 34, 56)
    assert dt.time('00:00:00') == time(0, 0, 0)
    with pytest.raises(ValueError):
        dt.time('1:30:00 PM')
    with pytest.raises(ValueError):
        dt.time('25:00:30')
    with pytest.raises(ValueError):
        dt.time('abc')

def test_hostname():
    assert dt.hostname('foo') == dt.Hostname('foo')
    assert dt.hostname(b'foo.bar') == dt.Hostname('foo.bar')
    assert dt.hostname('localhost') == dt.Hostname('localhost')
    assert dt.hostname('f'*63 + '.o') == dt.Hostname('f'*63 + '.o')
    assert dt.hostname('f'*63 + '.oo') == dt.Hostname('f'*63 + '.oo')
    with pytest.raises(ValueError):
        dt.hostname('foo.')
    with pytest.raises(ValueError):
        dt.hostname('.foo.')
    with pytest.raises(ValueError):
        dt.hostname('-foo.bar')
    with pytest.raises(ValueError):
        dt.hostname('foo.bar-')
    with pytest.raises(ValueError):
        dt.hostname('foo.bar-')
    with pytest.raises(ValueError):
        dt.hostname('f'*64 + '.o')
    with pytest.raises(ValueError):
        dt.hostname('foo.bar.'*32 + '.com')

def test_network_ipv4():
    assert dt.network('127.0.0.0/8') == dt.IPv4Network('127.0.0.0/8')
    assert dt.network(b'127.0.0.0/8') == dt.IPv4Network('127.0.0.0/8')
    with pytest.raises(ValueError):
        dt.network('foo')

def test_network_ipv6():
    assert dt.network('::/8') == dt.IPv6Network('::/8')
    assert dt.network(b'::/8') == dt.IPv6Network('::/8')
    with pytest.raises(ValueError):
        dt.network('::/1000')

def test_address_ipv4():
    assert dt.address('127.0.0.1') == dt.IPv4Address('127.0.0.1')
    assert dt.address(b'127.0.0.1:80') == dt.IPv4Port('127.0.0.1:80')
    with pytest.raises(ValueError):
        dt.address('abc')
    with pytest.raises(ValueError):
        dt.address('google.com')
    with pytest.raises(ValueError):
        dt.address('127.0.0.1:100000')

def test_address_ipv6():
    assert dt.address('::1') == dt.IPv6Address('::1')
    assert dt.address('[::1]') == dt.IPv6Port('::1')
    assert dt.address('[::1]:80') == dt.IPv6Port('[::1]:80')
    assert dt.address('2001:0db8:85a3:0000:0000:8a2e:0370:7334') == dt.IPv6Address('2001:db8:85a3::8a2e:370:7334')
    assert dt.address('[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:22') == dt.IPv6Port('[2001:db8:85a3::8a2e:370:7334]:22')
    assert dt.address('[fe80::7334]:22') == dt.IPv6Port('[fe80::7334]:22')
    with pytest.raises(ValueError):
        dt.address('[::1]:100000')

def test_address_port_manipulation():
    addr = dt.address('127.0.0.1:80')
    assert str(addr) == '127.0.0.1:80'
    addr.port = None
    assert str(addr) == '127.0.0.1'

def test_address_geoip_countries():
    with mock.patch('lars.geoip._GEOIP_IPV4_GEO') as mock_db:
        mock_db.country_code_by_addr.return_value = 'AA'
        assert dt.address('127.0.0.1').country == 'AA'
    with mock.patch('lars.geoip._GEOIP_IPV6_GEO') as mock_db:
        mock_db.country_code_by_addr.return_value = 'BB'
        assert dt.address('::1').country == 'BB'

def test_address_geoip_cities():
    with mock.patch('lars.geoip._GEOIP_IPV4_GEO') as mock_db:
        mock_db.region_by_addr.return_value = {'region_name': 'AA'}
        assert dt.address('127.0.0.1').region == 'AA'
        mock_db.record_by_addr.return_value = {'city': 'Timbuktu'}
        assert dt.address('127.0.0.1').city == 'Timbuktu'
        mock_db.record_by_addr.return_value = {'longitude': 1, 'latitude': 2}
        assert dt.address('127.0.0.1').coords == geoip.GeoCoord(1, 2)
        mock_db.record_by_addr.return_value = None
        assert dt.address('127.0.0.1').city is None
        assert dt.address('127.0.0.1').coords is None
    with mock.patch('lars.geoip._GEOIP_IPV6_GEO') as mock_db:
        mock_db.region_by_addr.return_value = {'region_name': 'BB'}
        assert dt.address('::1').region == 'BB'
        mock_db.record_by_addr.return_value = {'city': 'Transylvania'}
        assert dt.address('::1').city == 'Transylvania'
        mock_db.record_by_addr.return_value = {'longitude': 3, 'latitude': 4}
        assert dt.address('::1').coords == geoip.GeoCoord(3, 4)
        mock_db.record_by_addr.return_value = None
        assert dt.address('::1').city is None
        assert dt.address('::1').coords is None

def test_address_geoip_isp():
    with mock.patch('lars.geoip._GEOIP_IPV4_ISP') as mock_db:
        mock_db.org_by_addr.return_value = 'Internet 404'
        assert dt.address('127.0.0.1').isp == 'Internet 404'
    with mock.patch('lars.geoip._GEOIP_IPV6_ISP') as mock_db:
        mock_db.org_by_addr.return_value = 'Internet 404'
        assert dt.address('::1').isp == 'Internet 404'

def test_address_geoip_org():
    with mock.patch('lars.geoip._GEOIP_IPV4_ORG') as mock_db:
        mock_db.org_by_addr.return_value = 'Acme Inc.'
        assert dt.address('127.0.0.1').org == 'Acme Inc.'
    with mock.patch('lars.geoip._GEOIP_IPV6_ORG') as mock_db:
        mock_db.org_by_addr.return_value = 'Acme Inc.'
        assert dt.address('::1').org == 'Acme Inc.'

def test_resolving():
    assert dt.hostname('localhost').address == dt.IPv4Address('127.0.0.1')
    # This is a bit of a hack; largely depends on the system that's running the
    # tests whether these work or not (localhost can be called all sorts of
    # things) but the values below work for vanilla Ubuntu hosts and Travis
    # CI's VMs
    assert dt.hostname('localhost').address.hostname in (
            dt.hostname('localhost'),
            dt.hostname('localhost.localdomain'),
            )
    assert dt.hostname('test.invalid').address is None
    assert dt.address('127.0.0.1').hostname in (
            dt.hostname('localhost'),
            dt.hostname('localhost.localdomain'),
            )

def test_address():
    with mock.patch('lars.dns.from_address') as from_address:
        from_address.return_value = '0.0.0.0'
        assert dt.address('0.0.0.0').hostname is None
        from_address.return_value = '::'
        assert dt.address('::').hostname is None

def test_sqlite_adapters():
    pp = sqlite3.PrepareProtocol
    assert sqlite3.adapters[(dt.Date, pp)](dt.Date(2000, 1, 1)) == '2000-01-01'
    assert sqlite3.adapters[(dt.Time, pp)](dt.Time(12, 34, 56)) == '12:34:56'
    assert sqlite3.adapters[(dt.DateTime, pp)](dt.DateTime(2000, 1, 1, 12, 34, 56)) == '2000-01-01 12:34:56'
    assert sqlite3.adapters[(dt.DateTime, pp)](dt.DateTime(2000, 1, 1, 12, 34, 56, 789)) == '2000-01-01 12:34:56.000789'

def test_sqlite_converters():
    assert sqlite3.converters['DATE'](b'2000-01-01') == dt.Date(2000, 1, 1)
    assert sqlite3.converters['TIME'](b'12:34:56') == dt.Time(12, 34, 56)
    assert sqlite3.converters['TIMESTAMP'](b'2000-01-01 12:34:56') == dt.DateTime(2000, 1, 1, 12, 34, 56)
    assert sqlite3.converters['TIMESTAMP'](b'2000-01-01 12:34:56.000789') == dt.DateTime(2000, 1, 1, 12, 34, 56, 789)

