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

from datetime import datetime, date, time

from nose.tools import assert_raises

from www2csv import w3c, datatypes


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


def test_directive_regexes():
    assert w3c.W3CWrapper.VERSION_RE.match('#Version: 1.0')
    assert w3c.W3CWrapper.VERSION_RE.match('# VERSION : 1.0')
    assert w3c.W3CWrapper.VERSION_RE.match('# version:100.99')
    assert not w3c.W3CWrapper.VERSION_RE.match('#Version: foo')
    assert w3c.W3CWrapper.START_DATE_RE.match('#Start-Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.START_DATE_RE.match('# START-DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.START_DATE_RE.match('# start-date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.START_DATE_RE.match('#Start-Date: 2012-06-01')
    assert w3c.W3CWrapper.END_DATE_RE.match('#End-Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.END_DATE_RE.match('# END-DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.END_DATE_RE.match('# end-date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.END_DATE_RE.match('#End-Date: 2012-06-01')
    assert w3c.W3CWrapper.DATE_RE.match('#Date: 2000-01-01 00:00:00')
    assert w3c.W3CWrapper.DATE_RE.match('# DATE : 2012-04-28 23:59:59')
    assert w3c.W3CWrapper.DATE_RE.match('# date:1976-01-01 09:00:00')
    assert not w3c.W3CWrapper.DATE_RE.match('#Date: 2012-06-01')
    assert w3c.W3CWrapper.SOFTWARE_RE.match('#Software: foo')
    assert w3c.W3CWrapper.SOFTWARE_RE.match('# software : bar')
    assert w3c.W3CWrapper.REMARK_RE.match('#Remark: bar')
    assert w3c.W3CWrapper.REMARK_RE.match('# remark : bar')
    assert w3c.W3CWrapper.FIELDS_RE.match('#Fields: foo cs-foo rs(foo)')
    assert w3c.W3CWrapper.FIELDS_RE.match('# fields : x(bar) date time s-bar')
    assert w3c.W3CWrapper.FIELD_RE.match('foo')
    assert w3c.W3CWrapper.FIELD_RE.match('cs-foo')
    assert w3c.W3CWrapper.FIELD_RE.match('rs(foo)')
    assert w3c.W3CWrapper.FIELD_RE.match('x(bar)')
    # We can't deny invalid prefixes as the standard doesn't limit what
    # characters may appear in an identifier (and MS has already used the "-"
    # delimiter in several of their non-listed fields), so the best we can do
    # is match and make sure the prefix stays None
    assert w3c.W3CWrapper.FIELD_RE.match('foo(bar)').group('prefix') is None
    assert w3c.W3CWrapper.FIELD_RE.match('foo(bar)').group('identifier') == 'foo(bar)'

def test_sanitize_name():
    assert w3c.sanitize_name('foo') == 'foo'
    assert w3c.sanitize_name('FOO') == 'FOO'
    assert w3c.sanitize_name(' foo ') == '_foo_'
    assert w3c.sanitize_name('rs-date') == 'rs_date'
    assert w3c.sanitize_name('cs(User-Agent)') == 'cs_User_Agent_'
    assert_raises(ValueError, w3c.sanitize_name, '')

def test_url_parse():
    assert w3c.url_parse('-') is None
    assert w3c.url_parse('foo') == datatypes.Url('', '', 'foo', '', '', '')
    assert w3c.url_parse('//foo/bar') == datatypes.Url('', 'foo', '/bar', '', '', '')
    assert w3c.url_parse('http://foo/') == datatypes.Url('http', 'foo', '/', '', '', '')
    assert w3c.url_parse('http://foo/bar?baz=quux') == datatypes.Url('http', 'foo', '/bar', '', 'baz=quux', '')
    assert w3c.url_parse('https://foo/bar#baz') == datatypes.Url('https', 'foo', '/bar', '', '', 'baz')

def test_int_parse():
    assert w3c.int_parse('-') is None
    assert w3c.int_parse('0') == 0
    assert w3c.int_parse('-1') == -1
    assert w3c.int_parse('101') == 101
    assert_raises(ValueError, w3c.int_parse, 'abc')

def test_fixed_parse():
    assert w3c.fixed_parse('-') is None
    assert w3c.fixed_parse('0') == 0.0
    assert w3c.fixed_parse('0.') == 0.0
    assert w3c.fixed_parse('0.0') == 0.0
    assert w3c.fixed_parse('-101.5') == -101.5
    assert_raises(ValueError, w3c.fixed_parse, 'abc')

def test_date_parse():
    assert w3c.date_parse('-') is None
    assert w3c.date_parse('2000-01-01') == date(2000, 1, 1)
    assert w3c.date_parse('1986-02-28') == date(1986, 2, 28)
    assert_raises(ValueError, w3c.date_parse, '1 Jan 2001')
    assert_raises(ValueError, w3c.date_parse, '2000-01-32')
    assert_raises(ValueError, w3c.date_parse, 'abc')

def test_time_parse():
    assert w3c.time_parse('-') is None
    assert w3c.time_parse('12:34:56') == time(12, 34, 56)
    assert w3c.time_parse('00:00:00') == time(0, 0, 0)
    assert_raises(ValueError, w3c.time_parse, '1:30:00 PM')
    assert_raises(ValueError, w3c.time_parse, '25:00:30')
    assert_raises(ValueError, w3c.time_parse, 'abc')

def test_string_parse():
    assert w3c.string_parse('-') is None
    assert w3c.string_parse('foo') == 'foo'
    assert w3c.string_parse('foo+bar') == 'foo bar'
    assert w3c.string_parse('%28foo+bar%29') == '(foo bar)'
    assert w3c.string_parse('(foo;+bar;+baz)') == '(foo; bar; baz)'
    assert w3c.string_parse('"foo"') == 'foo'
    assert w3c.string_parse('"foo bar"') == 'foo bar'
    assert w3c.string_parse('"""foo"""') == '"foo"'
    assert w3c.string_parse('""') == ''
    assert w3c.string_parse('"""') == '"'
    assert w3c.string_parse('""""') == '"'

def test_name_parse():
    assert w3c.name_parse('-') is None
    assert w3c.name_parse('foo') == 'foo'
    assert w3c.name_parse('foo.bar') == 'foo.bar'
    assert w3c.name_parse('127.0.0.1') == '127.0.0.1'
    assert w3c.name_parse('f'*63 + '.o') == 'f'*63 + '.o'
    assert w3c.name_parse('f'*63 + '.oo') == 'f'*63 + '.oo'
    assert_raises(ValueError, w3c.name_parse, 'foo.')
    assert_raises(ValueError, w3c.name_parse, '.foo.')
    assert_raises(ValueError, w3c.name_parse, '-foo.bar')
    assert_raises(ValueError, w3c.name_parse, 'foo.bar-')
    assert_raises(ValueError, w3c.name_parse, 'foo.bar-')
    assert_raises(ValueError, w3c.name_parse, 'f'*64 + '.o')
    assert_raises(ValueError, w3c.name_parse, 'foo.bar.'*32 + '.com')

def test_address_parse():
    assert w3c.address_parse('-') is None
    # All possible representations of an IPv4 address (including silly ones)
    assert str(w3c.address_parse('127.0.0.1')) == '127.0.0.1'
    assert str(w3c.address_parse('127.0.0.1:80')) == '127.0.0.1:80'
    assert str(w3c.address_parse('::1')) == '::1'
    assert str(w3c.address_parse('[::1]')) == '::1'
    assert str(w3c.address_parse('[::1]:80')) == '[::1]:80'
    assert str(w3c.address_parse('2001:0db8:85a3:0000:0000:8a2e:0370:7334')) == '2001:db8:85a3::8a2e:370:7334'
    assert str(w3c.address_parse('[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:22')) == '[2001:db8:85a3::8a2e:370:7334]:22'
    assert str(w3c.address_parse('[fe80::7334]:22')) == '[fe80::7334]:22'
    assert_raises(ValueError, w3c.address_parse, 'abc')
    assert_raises(ValueError, w3c.address_parse, 'google.com')
    assert_raises(ValueError, w3c.address_parse, '127.0.0.1:100000')
    assert_raises(ValueError, w3c.address_parse, '[::1]:100000')

def test_wrapper():
    source = INTERNET_EXAMPLE.splitlines(True)
    wrapper = w3c.W3CWrapper(source)
    row = None
    for count, row in enumerate(wrapper):
        assert wrapper.version == '1.0'
        assert wrapper.software == 'Microsoft Internet Information Services 6.0'
        assert wrapper.date == datetime(2002, 5, 24, 20, 18, 1)
        assert wrapper.fields == [
            'date', 'time', 'c-ip', 'cs-username', 's-ip', 's-port',
            'cs-method', 'cs-uri-stem', 'cs-uri-query', 'sc-status',
            'sc-bytes', 'cs-bytes', 'time-taken', 'cs(User-Agent)',
            'cs(Referrer)',
            ]
        assert row.date == date(2002, 5, 24)
        assert row.time == time(20, 18, 1)
        assert str(row.c_ip) == '172.224.24.114'
        assert row.cs_username is None
        assert str(row.s_ip) == '206.73.118.24'
        assert row.s_port == 80
        assert row.cs_method == 'GET'
        assert str(row.cs_uri_stem) == '/Default.htm'
        assert row.cs_uri_query is None
        assert row.sc_status == 200
        assert row.sc_bytes == 7930
        assert row.cs_bytes == 248
        assert row.time_taken == 31.0
        assert row.cs_User_Agent == 'Mozilla/4.0 (compatible; MSIE 5.01; Windows 2000 Server)'
        assert row.cs_Referrer == 'http://64.224.24.114/'
    assert row
    assert count == 0
    source = INTRANET_EXAMPLE.splitlines(True)
    wrapper = w3c.W3CWrapper(source)
    row = None
    for count, row in enumerate(wrapper):
        assert wrapper.fields == [
            'date', 'time', 'c-ip', 'cs-username', 's-ip', 's-port',
            'cs-method', 'cs-uri-stem', 'cs-uri-query', 'sc-status',
            'cs(User-Agent)',
            ]
        assert row.date == date(2002, 5, 2)
        assert row.time == time(17, 42, 15)
        assert str(row.c_ip) == '172.22.255.255'
        assert row.cs_username is None
        assert str(row.s_ip) == '172.30.255.255'
        assert row.s_port == 80
        assert row.cs_method == 'GET'
        assert str(row.cs_uri_stem) == '/images/picture.jpg'
        assert row.cs_uri_query is None
        assert row.sc_status == 200
        assert row.cs_User_Agent == 'Mozilla/4.0 (compatible;MSIE 5.5; Windows 2000 Server)'
    assert row
    assert count == 0

