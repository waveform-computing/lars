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

import sys
import os
import shutil
import sqlite3
from datetime import datetime, date, time
from ipaddress import ip_address, IPv4Address, IPv6Address

import pytest
import mock

from www2csv import datatypes, geoip


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
    assert datatypes.sanitize_name('foo') == 'foo'
    assert datatypes.sanitize_name('FOO') == 'FOO'
    assert datatypes.sanitize_name(' foo ') == '_foo_'
    assert datatypes.sanitize_name('rs-date') == 'rs_date'
    assert datatypes.sanitize_name('cs(User-Agent)') == 'cs_User_Agent_'
    with pytest.raises(ValueError):
        datatypes.sanitize_name('')

def test_url():
    assert datatypes.url('foo') == datatypes.Url('', '', 'foo', '', '', '')
    assert datatypes.url('//foo/bar') == datatypes.Url('', 'foo', '/bar', '', '', '')
    assert datatypes.url('http://foo/') == datatypes.Url('http', 'foo', '/', '', '', '')
    assert datatypes.url('http://foo/bar?baz=quux') == datatypes.Url('http', 'foo', '/bar', '', 'baz=quux', '')
    assert datatypes.url('https://foo/bar#baz') == datatypes.Url('https', 'foo', '/bar', '', '', 'baz')
    u = datatypes.url('http://localhost/foo/bar#baz')
    assert u.scheme == 'http'
    assert u.netloc == 'localhost'
    assert u.path == '/foo/bar'
    assert u.fragment == 'baz'
    assert u.username is None
    assert u.password is None
    assert u.port is None
    assert u.hostname == datatypes.hostname('localhost')
    assert u.hostname.address == datatypes.address('127.0.0.1')

def test_row():
    NewRow = datatypes.row('foo', 'bar', 'baz')
    assert NewRow._fields == ('foo', 'bar', 'baz')
    assert NewRow(1, 2, 3) == (1, 2, 3)
    assert NewRow(1, 2, 3).foo == 1
    assert NewRow(1, 2, 3).bar == 2
    assert NewRow(1, 2, 3).baz == 3

def test_datetime():
    assert datatypes.datetime('2000-01-01 12:34:56') == datetime(2000, 1, 1, 12, 34, 56)
    assert datatypes.datetime('1986-02-28 00:00:00') == datetime(1986, 2, 28)
    with pytest.raises(ValueError):
        datatypes.datetime('2000-01-32 12:34:56')
    with pytest.raises(ValueError):
        datatypes.datetime('2000-01-30 12:34:56 PM')
    with pytest.raises(ValueError):
        datatypes.datetime('foo')

def test_date():
    assert datatypes.date('2000-01-01') == date(2000, 1, 1)
    assert datatypes.date('1986-02-28') == date(1986, 2, 28)
    with pytest.raises(ValueError):
        datatypes.date('1 Jan 2001')
    with pytest.raises(ValueError):
        datatypes.date('2000-01-32')
    with pytest.raises(ValueError):
        datatypes.date('abc')

def test_time():
    assert datatypes.time('12:34:56') == time(12, 34, 56)
    assert datatypes.time('00:00:00') == time(0, 0, 0)
    with pytest.raises(ValueError):
        datatypes.time('1:30:00 PM')
    with pytest.raises(ValueError):
        datatypes.time('25:00:30')
    with pytest.raises(ValueError):
        datatypes.time('abc')

def test_path(tmpdir):
    assert datatypes.path('bin') == 'bin'
    assert datatypes.path('bin').abspath == os.path.join(os.getcwd(), 'bin')
    assert datatypes.path(tmpdir).exists
    assert datatypes.path(tmpdir).atime == datetime.utcfromtimestamp(tmpdir.stat().atime)
    assert datatypes.path(tmpdir).mtime == datetime.utcfromtimestamp(tmpdir.stat().mtime)
    assert datatypes.path(tmpdir).ctime == datetime.utcfromtimestamp(tmpdir.stat().ctime)
    assert datatypes.path(tmpdir).size == tmpdir.stat().size
    assert not datatypes.path(tmpdir).isfile
    assert not datatypes.path(tmpdir).islink
    assert datatypes.path(tmpdir).isdir
    assert datatypes.path(tmpdir).realpath == tmpdir.realpath()
    tmpdir.join('foo').mksymlinkto(tmpdir)
    tmpdir.join('bar').mksymlinkto(tmpdir.join('foo'))
    tmpdir.join('foo').remove()
    assert not datatypes.path(tmpdir.join('bar')).exists
    assert datatypes.path(tmpdir.join('bar')).lexists

@pytest.mark.skipif('not sys.platform.startswith("win")')
def test_path_win():
    assert datatypes.path('\\') == '\\'
    assert datatypes.path('\\bin') == '\\bin'
    assert datatypes.path('C:\\foo\\bar').drive == 'C:'
    assert datatypes.path('\\foo\\bar').basename == 'bar'
    assert datatypes.path('\\foo\\bar').basename_no_ext == 'bar'
    assert datatypes.path('\\foo\\bar.baz').basename == 'bar.baz'
    assert datatypes.path('\\foo\\bar.baz').basename_no_ext == 'bar'
    assert datatypes.path('\\foo\\bar.baz').ext == '.baz'
    assert datatypes.path('\\foo\\bar').dirname == '\\foo'
    assert datatypes.path('C:\\foo\\bar').isabs
    assert not datatypes.path('foo\\bar').isabs
    assert datatypes.path('foo\\bar').abspath.relative(os.getcwd()) == 'foo\\bar'
    with pytest.raises(ValueError):
        datatypes.path(r'2:\foo')
    with pytest.raises(ValueError):
        datatypes.path('<foo>')
    with pytest.raises(ValueError):
        datatypes.path('foo*')
    assert datatypes.path('\\FOO\\BAR').normcase == '\\foo\\bar'
    assert datatypes.path('\\FOO\\.\\BAR').normpath == '\\FOO\\BAR'

@pytest.mark.skipif('sys.platform.startswith("win")')
def test_path_posix():
    assert datatypes.path('/') == '/'
    assert datatypes.path('/bin') == '/bin'
    assert datatypes.path('/foo/bar').basename == 'bar'
    assert datatypes.path('/foo/bar').basename_no_ext == 'bar'
    assert datatypes.path('/foo/bar.baz').basename == 'bar.baz'
    assert datatypes.path('/foo/bar.baz').basename_no_ext == 'bar'
    assert datatypes.path('/foo/bar.baz').ext == '.baz'
    assert datatypes.path('/foo/bar').dirname == '/foo'
    assert datatypes.path('/foo/bar').isabs
    assert not datatypes.path('foo/bar').isabs
    assert datatypes.path('foo/bar').abspath.relative(os.getcwd()) == 'foo/bar'
    # As we're in a temp directory, it can't be a mount
    assert not datatypes.path('.').ismount
    with pytest.raises(ValueError):
        datatypes.path('<foo>')
    with pytest.raises(ValueError):
        datatypes.path('foo*')
    assert datatypes.path('/FOO/BAR').normcase == '/FOO/BAR'
    assert datatypes.path('/FOO//.//BAR').normpath == '/FOO/BAR'

def test_hostname():
    assert datatypes.hostname('foo') == datatypes.Hostname('foo')
    assert datatypes.hostname('foo.bar') == datatypes.Hostname('foo.bar')
    assert datatypes.hostname('localhost') == datatypes.Hostname('localhost')
    assert datatypes.hostname('f'*63 + '.o') == datatypes.Hostname('f'*63 + '.o')
    assert datatypes.hostname('f'*63 + '.oo') == datatypes.Hostname('f'*63 + '.oo')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.')
    with pytest.raises(ValueError):
        datatypes.hostname('.foo.')
    with pytest.raises(ValueError):
        datatypes.hostname('-foo.bar')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar-')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar-')
    with pytest.raises(ValueError):
        datatypes.hostname('f'*64 + '.o')
    with pytest.raises(ValueError):
        datatypes.hostname('foo.bar.'*32 + '.com')

def test_network_ipv4():
    assert datatypes.network('127.0.0.0/8') == datatypes.IPv4Network('127.0.0.0/8')
    assert datatypes.network(b'127.0.0.0/8') == datatypes.IPv4Network('127.0.0.0/8')
    with pytest.raises(ValueError):
        datatypes.network('foo')

def test_network_ipv6():
    assert datatypes.network('::/8') == datatypes.IPv6Network('::/8')
    assert datatypes.network(b'::/8') == datatypes.IPv6Network('::/8')
    with pytest.raises(ValueError):
        datatypes.network('::/1000')

def test_address_ipv4():
    assert datatypes.address('127.0.0.1') == datatypes.IPv4Address('127.0.0.1')
    assert datatypes.address(b'127.0.0.1:80') == datatypes.IPv4Port('127.0.0.1:80')
    with pytest.raises(ValueError):
        datatypes.address('abc')
    with pytest.raises(ValueError):
        datatypes.address('google.com')
    with pytest.raises(ValueError):
        datatypes.address('127.0.0.1:100000')

def test_address_ipv6():
    assert datatypes.address('::1') == datatypes.IPv6Address('::1')
    assert datatypes.address('[::1]') == datatypes.IPv6Port('::1')
    assert datatypes.address('[::1]:80') == datatypes.IPv6Port('[::1]:80')
    assert datatypes.address('2001:0db8:85a3:0000:0000:8a2e:0370:7334') == datatypes.IPv6Address('2001:db8:85a3::8a2e:370:7334')
    assert datatypes.address('[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:22') == datatypes.IPv6Port('[2001:db8:85a3::8a2e:370:7334]:22')
    assert datatypes.address('[fe80::7334]:22') == datatypes.IPv6Port('[fe80::7334]:22')
    with pytest.raises(ValueError):
        datatypes.address('[::1]:100000')

def test_address_port_manipulation():
    addr = datatypes.address('127.0.0.1:80')
    assert str(addr) == '127.0.0.1:80'
    addr.port = None
    assert str(addr) == '127.0.0.1'

def test_address_geoip_countries():
    with mock.patch('tests.test_datatypes.geoip._GEOIP_IPV4_DATABASE') as mock_db:
        mock_db.country_code_by_addr.return_value = 'AA'
        assert datatypes.address('127.0.0.1').country == 'AA'
    with mock.patch('tests.test_datatypes.geoip._GEOIP_IPV6_DATABASE') as mock_db:
        mock_db.country_code_by_addr.return_value = 'BB'
        assert datatypes.address('::1').country == 'BB'

def test_address_geoip_cities():
    with mock.patch('tests.test_datatypes.geoip._GEOIP_IPV4_DATABASE') as mock_db:
        mock_db.region_by_addr.return_value = {'region_name': 'AA'}
        assert datatypes.address('127.0.0.1').region == 'AA'
        mock_db.record_by_addr.return_value = {'city': 'Timbuktu'}
        assert datatypes.address('127.0.0.1').city == 'Timbuktu'
        mock_db.record_by_addr.return_value = {'longitude': 1, 'latitude': 2}
        assert datatypes.address('127.0.0.1').coords == geoip.GeoCoord(1, 2)
        mock_db.record_by_addr.return_value = None
        assert datatypes.address('127.0.0.1').city is None
        assert datatypes.address('127.0.0.1').coords is None
    with mock.patch('tests.test_datatypes.geoip._GEOIP_IPV6_DATABASE') as mock_db:
        mock_db.region_by_addr.return_value = {'region_name': 'BB'}
        assert datatypes.address('::1').region == 'BB'
        mock_db.record_by_addr.return_value = {'city': 'Transylvania'}
        assert datatypes.address('::1').city == 'Transylvania'
        mock_db.record_by_addr.return_value = {'longitude': 3, 'latitude': 4}
        assert datatypes.address('::1').coords == geoip.GeoCoord(3, 4)
        mock_db.record_by_addr.return_value = None
        assert datatypes.address('::1').city is None
        assert datatypes.address('::1').coords is None

def test_resolving():
    assert datatypes.hostname('localhost').address == datatypes.IPv4Address('127.0.0.1')
    assert datatypes.hostname('localhost') == datatypes.hostname('localhost').address.hostname
    assert datatypes.hostname('test.invalid').address is None
    assert datatypes.address('127.0.0.1').hostname == datatypes.hostname('localhost')
    assert datatypes.address('::1').hostname == datatypes.hostname('ip6-localhost')

def test_address():
    with mock.patch('tests.test_datatypes.datatypes.dns.from_address') as from_address:
        from_address.return_value = '0.0.0.0'
        assert datatypes.address('0.0.0.0').hostname is None
        from_address.return_value = '::'
        assert datatypes.address('::').hostname is None

def test_sqlite_adapters():
    pp = sqlite3.PrepareProtocol
    assert sqlite3.adapters[(datatypes.Date, pp)](datatypes.Date(2000, 1, 1)) == '2000-01-01'
    assert sqlite3.adapters[(datatypes.Time, pp)](datatypes.Time(12, 34, 56)) == '12:34:56'
    assert sqlite3.adapters[(datatypes.DateTime, pp)](datatypes.DateTime(2000, 1, 1, 12, 34, 56)) == '2000-01-01 12:34:56'
    assert sqlite3.adapters[(datatypes.DateTime, pp)](datatypes.DateTime(2000, 1, 1, 12, 34, 56, 789)) == '2000-01-01 12:34:56.000789'

def test_sqlite_converters():
    assert sqlite3.converters['DATE']('2000-01-01') == datatypes.Date(2000, 1, 1)
    assert sqlite3.converters['TIME']('12:34:56') == datatypes.Time(12, 34, 56)
    assert sqlite3.converters['TIMESTAMP']('2000-01-01 12:34:56') == datatypes.DateTime(2000, 1, 1, 12, 34, 56)
    assert sqlite3.converters['TIMESTAMP']('2000-01-01 12:34:56.000789') == datatypes.DateTime(2000, 1, 1, 12, 34, 56, 789)

