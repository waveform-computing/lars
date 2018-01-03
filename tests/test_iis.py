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

import pytest

from lars import iis, datatypes as dt


# Make Py2 str same as Py3
str = type('')


INTERNET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Date: 2002-05-24 20:18:01
#Remark: This is some simple test data adapted from http://www.microsoft.com/technet/prodtechnol/WindowsServer2003/Library/IIS/ffdd7079-47be-4277-921f-7a3a6e610dcb.mspx
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

INTRANET_EXAMPLE = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Start-Date: 2002-05-02 17:42:15
#End-Date: 2002-05-02 18:40:00
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status cs(User-Agent)
2002-05-02 17:42:15 172.22.255.255 - 172.30.255.255 80 GET /images/picture.jpg - 200 Mozilla/4.0+(compatible;MSIE+5.5;+Windows+2000+Server)
"""

BAD_VERSION = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 2.0
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

MISSING_VERSION = """\
#Software: Microsoft Internet Information Services 6.0
#Date: 2002-05-24 20:18:01
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

REPEAT_VERSION = """\
#Software: Microsoft Internet Information Services 6.0
#Version: 1.0
#Version: 1.0
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

REPEAT_FIELDS = """\
#Software: Microsoft Internet Information Services 6.0
#Date: 2002-05-24 20:18:01
#Fields: time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
#Fields: date time c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

MISSING_FIELDS = """\
#Software: Microsoft Internet Information Services 6.0
#Date: 2002-05-24 20:18:01
#Version: 1.0
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

DUPLICATE_FIELD_NAMES = """\
#Software: Microsoft Internet Information Services 6.0
#Date: 2002-05-24 20:18:01
#Version: 1.0
#Fields: date time c-ip c-ip cs-username s-ip s-port cs-method cs-uri-stem cs-uri-query sc-status sc-bytes cs-bytes time-taken cs(User-Agent) cs(Referrer) 
2002-05-24 20:18:01 172.224.24.114 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

INVALID_DIRECTIVE = """\
#Software: Microsoft Internet Information Services 6.0
#Date: 2002-05-24 20:18:01
#Foo: Bar
#Version: 1.0
2002-05-24 20:18:01 172.224.24.114 - 206.73.118.24 80 GET /Default.htm - 200 7930 248 31 Mozilla/4.0+(compatible;+MSIE+5.01;+Windows+2000+Server) http://64.224.24.114/
"""

BAD_DATA_EXAMPLE_01 = """\
#Version: 1.0
#Date: 2002-05-24 20:18:01
#Fields: date time c-ip
2002-05-30 20:18:01 172.224.24.300
"""

BAD_DATA_EXAMPLE_02 = """\
#Version: 1.0
#Date: 2002-05-24 20:18:01
#Fields: date time c-ip
2002-05-30 20:18:01 foo.bar
"""


def test_directive_regexes():
    assert iis.IISSource.VERSION_RE.match('#Version: 1.0')
    assert iis.IISSource.VERSION_RE.match('# VERSION : 1.0')
    assert iis.IISSource.VERSION_RE.match('# version:100.99')
    assert not iis.IISSource.VERSION_RE.match('#Version: foo')
    assert iis.IISSource.START_DATE_RE.match('#Start-Date: 2000-01-01 00:00:00')
    assert iis.IISSource.START_DATE_RE.match('# START-DATE : 2012-04-28 23:59:59')
    assert iis.IISSource.START_DATE_RE.match('# start-date:1976-01-01 09:00:00')
    assert not iis.IISSource.START_DATE_RE.match('#Start-Date: 2012-06-01')
    assert iis.IISSource.END_DATE_RE.match('#End-Date: 2000-01-01 00:00:00')
    assert iis.IISSource.END_DATE_RE.match('# END-DATE : 2012-04-28 23:59:59')
    assert iis.IISSource.END_DATE_RE.match('# end-date:1976-01-01 09:00:00')
    assert not iis.IISSource.END_DATE_RE.match('#End-Date: 2012-06-01')
    assert iis.IISSource.DATE_RE.match('#Date: 2000-01-01 00:00:00')
    assert iis.IISSource.DATE_RE.match('# DATE : 2012-04-28 23:59:59')
    assert iis.IISSource.DATE_RE.match('# date:1976-01-01 09:00:00')
    assert not iis.IISSource.DATE_RE.match('#Date: 2012-06-01')
    assert iis.IISSource.SOFTWARE_RE.match('#Software: foo')
    assert iis.IISSource.SOFTWARE_RE.match('# software : bar')
    assert iis.IISSource.REMARK_RE.match('#Remark: bar')
    assert iis.IISSource.REMARK_RE.match('# remark : bar')
    assert iis.IISSource.FIELDS_RE.match('#Fields: foo cs-foo rs(foo)')
    assert iis.IISSource.FIELDS_RE.match('# fields : x(bar) date time s-bar')
    assert iis.IISSource.FIELD_RE.match('foo')
    assert iis.IISSource.FIELD_RE.match('cs-foo')
    assert iis.IISSource.FIELD_RE.match('rs(foo)')
    assert iis.IISSource.FIELD_RE.match('x(bar)')
    # We can't deny invalid prefixes as the standard doesn't limit what
    # characters may appear in an identifier (and MS has already used the "-"
    # delimiter in several of their non-listed fields), so the best we can do
    # is match and make sure the prefix stays None
    assert iis.IISSource.FIELD_RE.match('foo(bar)').group('prefix') is None
    assert iis.IISSource.FIELD_RE.match('foo(bar)').group('identifier') == 'foo(bar)'

def test_string_parse():
    assert iis._string_parse('-') is None
    assert iis._string_parse('foo') == 'foo'
    assert iis._string_parse('foo+bar') == 'foo bar'
    assert iis._string_parse('%28foo+bar%29') == '(foo bar)'
    assert iis._string_parse('(foo;+bar;+baz)') == '(foo; bar; baz)'
    assert iis._string_parse('"foo"') == 'foo'
    assert iis._string_parse('"foo bar"') == 'foo bar'
    assert iis._string_parse('"""foo"""') == '"foo"'
    assert iis._string_parse('""') == ''
    assert iis._string_parse('"""') == '"'
    assert iis._string_parse('""""') == '"'

def test_exceptions():
    exc = iis.IISError('Something went wrong!', 23)
    assert str(exc) == 'Line 23: Something went wrong!'
    exc = iis.IISError('Something else went wrong!')
    assert str(exc) == 'Something else went wrong!'

def test_source_normal():
    # Test two normal runs with INTERNET_EXAMPLE and INTRANET_EXAMPLE
    with iis.IISSource(INTERNET_EXAMPLE.splitlines(True)) as source:
        row = None
        for count, row in enumerate(source):
            assert source.version == '1.0'
            assert source.software == 'Microsoft Internet Information Services 6.0'
            assert source.date == dt.DateTime(2002, 5, 24, 20, 18, 1)
            assert source.fields == [
                'date', 'time', 'c-ip', 'cs-username', 's-ip', 's-port',
                'cs-method', 'cs-uri-stem', 'cs-uri-query', 'sc-status',
                'sc-bytes', 'cs-bytes', 'time-taken', 'cs(User-Agent)',
                'cs(Referrer)',
                ]
            assert row.date == dt.Date(2002, 5, 24)
            assert row.time == dt.Time(20, 18, 1)
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
            assert row.cs_Referrer == dt.url('http://64.224.24.114/')
        assert row
        assert count + 1 == source.count
    with iis.IISSource(INTRANET_EXAMPLE.splitlines(True)) as source:
        row = None
        for count, row in enumerate(source):
            assert source.fields == [
                'date', 'time', 'c-ip', 'cs-username', 's-ip', 's-port',
                'cs-method', 'cs-uri-stem', 'cs-uri-query', 'sc-status',
                'cs(User-Agent)',
                ]
            assert row.date == dt.Date(2002, 5, 2)
            assert row.time == dt.Time(17, 42, 15)
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
        assert count + 1 == source.count

def test_source_invalid_headers():
    with pytest.raises(iis.IISVersionError):
        with iis.IISSource(BAD_VERSION.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISVersionError):
        with iis.IISSource(REPEAT_VERSION.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISVersionError):
        with iis.IISSource(MISSING_VERSION.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISFieldsError):
        with iis.IISSource(REPEAT_FIELDS.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISFieldsError):
        with iis.IISSource(MISSING_FIELDS.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISFieldsError):
        with iis.IISSource(DUPLICATE_FIELD_NAMES.splitlines(True)) as source:
            for row in source:
                pass
    with pytest.raises(iis.IISDirectiveError):
        with iis.IISSource(INVALID_DIRECTIVE.splitlines(True)) as source:
            for row in source:
                pass

def test_source_warnings(recwarn):
    # Test data warnings - in this first case the line regex won't pick up that
    # the IP address is invalid, but the data conversion routine will
    with iis.IISSource(BAD_DATA_EXAMPLE_01.splitlines(True)) as source:
        for row in source:
            pass
    assert recwarn.pop(iis.IISWarning)
    recwarn.clear()
    # In this second example, the bad IP address will result in the line
    # failing to even match the line regex
    with iis.IISSource(BAD_DATA_EXAMPLE_02.splitlines(True)) as source:
        for row in source:
            pass
    assert recwarn.pop(iis.IISWarning)
