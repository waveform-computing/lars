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

from lars import apache, datatypes as dt


# Make Py2 str same as Py3
str = type('')


EXAMPLE_01 = """\
64.242.88.10 - - [07/Mar/2004:16:56:39 -0800] "GET /twiki/bin/view/Sandbox/WebHome?rev=1.6 HTTP/1.1" 200 8545
lordgun.org - foo [07/Mar/2004:17:01:53 -0800] "GET /razor.html HTTP/1.0" 302 2869
"""

EXAMPLE_02 = """\
78.86.48.95 - - [28/Oct/2011:00:00:05 +0100] "GET /template/images/ITSheader.jpg HTTP/1.1" 200 14745 "-" "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0; byond_4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; InfoPath.2; OfficeLiveConnector.1.5; OfficeLivePatch.1.3; .NET4.0E; .NET4.0C)"
217.129.225.117 - - [28/Oct/2011:00:00:07 +0100] "GET /images/spacer.gif HTTP/1.1" 200 43 "http://eprints.lse.ac.uk/33718/" "Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.2.23) Gecko/20110920 Firefox/3.6.23"
"""

EXAMPLE_03="""\
49600,80 1000
65000,80 2000
12345,443 65000
123,443 100
"""

EXAMPLE_04="""\
2004-03-07T16:56:39-0800 HTTP/1.0 GET /twiki/bin/view/Sandbox/WebHome?rev=1.6 200 8545
2004-03-07T17:01:53-0500 HTTP/1.1 HEAD /razor.html 302 2869
"""

MULTIPLE_REMOTE_HOSTS = """\
172.16.102.33, 41.231.129.45 - - [28/Oct/2011:00:00:09 +0100] "GET /images/header/studentServicesCentre.jpg HTTP/1.0" 200 33228 "http://www.m-omani.com/smf/index.php?topic=287.0" "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"
"""

INVALID_REMOTE_HOST = """\
this.is.an.extermely.long.hostname.with.altogether.far.too.many.parts.to.make.any.kind.of.sense.let.alone.permit.some.innocent.young.framework.from.possibly.having.a.hope.in.hell.of.parsing.it.without.throwing.a.major.wobbly.and.chucking.its.toys.out.of.the.pram - - [8/Oct/2001:12:45:09 +0100] "GET /images/header/studentServicesCentre.jpg HTTP/1.0" 200 33228 "http://www.m-omani.com/smf/index.php?topic=287.0" "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"
"""

INVALID_CHARS = """\
64.242.88.10 - - [07/Mar/2004:17:16:00 -0800] "GET /twiki/bin/search/Main/?scope=topic®ex=on&search=^g HTTP/1.1" 200 3675
"""

def test_english_locale():
    # Test we can simply instantiate the english-locale and that it has certain
    # attributes
    lt = apache.EnglishLocaleTime()
    attrs = ['a_month', 'a_weekday', 'f_month', 'f_weekday']
    for attr in attrs:
        assert hasattr(lt, attr)

def test_string_parse():
    assert apache._string_parse('-') is None
    assert apache._string_parse('') == ''
    assert apache._string_parse('abc') == 'abc'
    assert apache._string_parse('ab\\nc') == 'ab\nc'
    assert apache._string_parse('ab\\x0Ac') == 'ab\nc'
    assert apache._string_parse('foo\\tbar') == 'foo\tbar'
    assert apache._string_parse('foo\\x09bar') == 'foo\tbar'
    assert apache._string_parse('\\"foo\\"') == '"foo"'
    # Ensure the function simply leaves invalid escapes alone rather than
    # blowing up over them
    assert apache._string_parse('foo\\x') == 'foo\\x'
    assert apache._string_parse('foo\\xGG') == 'foo\\xGG'
    assert apache._string_parse('foo\\') == 'foo\\'

def test_time_parse_format():
    default = '[%d/%b/%Y:%H:%M:%S %z]'
    assert apache._time_parse_format('[25/Dec/1998:17:45:35 +0000]', default) == dt.DateTime(1998, 12, 25, 17, 45, 35)
    assert apache._time_parse_format('[25/Dec/1998:17:45:35 +0100]', default) == dt.DateTime(1998, 12, 25, 16, 45, 35)
    assert apache._time_parse_format('[4/Dec/2001:23:59:59 -0500]', default) == dt.DateTime(2001, 12, 5, 4, 59, 59)
    assert apache._time_parse_format('[4/Dec/2001:2:59:59 -0500]', default) == dt.DateTime(2001, 12, 4, 7, 59, 59)
    assert apache._time_parse_format('[4/Dec/2001:2:9:59 -0500]', default) == dt.DateTime(2001, 12, 4, 7, 9, 59)
    assert apache._time_parse_format('[4/Dec/2001:2:9:5 -0500]', default) == dt.DateTime(2001, 12, 4, 7, 9, 5)
    assert apache._time_parse_format('2000-01-01T12:34:56+0700', '%Y-%m-%dT%H:%M:%S%z') == dt.DateTime(2000, 1, 1, 5, 34, 56)
    with pytest.raises(ValueError):
        apache._time_parse_format('', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('012345678901234567890123456789', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('012345678901234567890123456', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[12345678901234567890123456', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1234567890123456789012345]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb67890123456789012345]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb/2000123456789012345]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb/2000:12345678901235]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb/2000:1:345678901235]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb/2000:1:3:4678901235]', default)
    with pytest.raises(ValueError):
        apache._time_parse_format('[1/Feb/2000:1:3:4 01235]', default)

def test_time_parse_common():
    assert apache._time_parse_common('[25/Dec/1998:17:45:35 +0000]') == dt.DateTime(1998, 12, 25, 17, 45, 35)
    assert apache._time_parse_common('[25/Dec/1998:17:45:35 +0100]') == dt.DateTime(1998, 12, 25, 16, 45, 35)
    assert apache._time_parse_common('[4/Dec/2001:23:59:59 -0500]') == dt.DateTime(2001, 12, 5, 4, 59, 59)
    assert apache._time_parse_common('[4/Dec/2001:2:59:59 -0500]') == dt.DateTime(2001, 12, 4, 7, 59, 59)
    assert apache._time_parse_common('[4/Dec/2001:2:9:59 -0500]') == dt.DateTime(2001, 12, 4, 7, 9, 59)
    assert apache._time_parse_common('[4/Dec/2001:2:9:5 -0500]') == dt.DateTime(2001, 12, 4, 7, 9, 5)
    with pytest.raises(ValueError):
        apache._time_parse_common('')
    with pytest.raises(ValueError):
        apache._time_parse_common('012345678901234567890123456789')
    with pytest.raises(ValueError):
        apache._time_parse_common('012345678901234567890123456')
    with pytest.raises(ValueError):
        apache._time_parse_common('[12345678901234567890123456')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1234567890123456789012345]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb67890123456789012345]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb/2000123456789012345]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb/2000:12345678901235]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb/2000:1:345678901235]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb/2000:1:3:4678901235]')
    with pytest.raises(ValueError):
        apache._time_parse_common('[1/Feb/2000:1:3:4 01235]')

def test_exceptions():
    exc = apache.ApacheError('Something went wrong!', 23)
    assert str(exc) == 'Line 23: Something went wrong!'
    exc = apache.ApacheError('Something else went wrong!')
    assert str(exc) == 'Something else went wrong!'

def test_source_common():
    with apache.ApacheSource(EXAMPLE_01.splitlines(True)) as source:
        row = None
        for count, row in enumerate(source):
            if count == 0:
                assert row.remote_host == dt.hostname('64.242.88.10')
                assert row.ident is None
                assert row.remote_user is None
                assert row.time == dt.DateTime(2004, 3, 8, 0, 56, 39)
                assert row.request == dt.Request('GET', dt.url('/twiki/bin/view/Sandbox/WebHome?rev=1.6'), 'HTTP/1.1')
                assert row.status == 200
                assert row.size == 8545
            elif count == 1:
                assert row.remote_host == dt.hostname('lordgun.org')
                assert row.ident is None
                assert row.remote_user == 'foo'
                assert row.time == dt.DateTime(2004, 3, 8, 1, 1, 53)
                assert row.request == dt.Request('GET', dt.url('/razor.html'), 'HTTP/1.0')
                assert row.status == 302
                assert row.size == 2869
            else:
                assert False
        assert row
        assert count == 1

def test_source_combined():
    with apache.ApacheSource(
            EXAMPLE_02.splitlines(True), log_format=apache.COMBINED) as source:
        row = None
        for count, row in enumerate(source):
            if count == 0:
                assert row.remote_host == dt.hostname('78.86.48.95')
                assert row.ident is None
                assert row.remote_user is None
                assert row.time == dt.DateTime(2011, 10, 27, 23, 0, 5)
                assert row.request == dt.Request('GET', dt.url('/template/images/ITSheader.jpg'), 'HTTP/1.1')
                assert row.status == 200
                assert row.size == 14745
                assert row.req_Referer is None
                assert row.req_User_agent == 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0; byond_4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; InfoPath.2; OfficeLiveConnector.1.5; OfficeLivePatch.1.3; .NET4.0E; .NET4.0C)'
            elif count == 1:
                assert row.remote_host == dt.hostname('217.129.225.117')
                assert row.ident is None
                assert row.remote_user is None
                assert row.time == dt.DateTime(2011, 10, 27, 23, 0, 7)
                assert row.request == dt.Request('GET', dt.url('/images/spacer.gif'), 'HTTP/1.1')
                assert row.status == 200
                assert row.size == 43
                assert row.req_Referer == dt.url('http://eprints.lse.ac.uk/33718/')
                assert row.req_User_agent == 'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.2.23) Gecko/20110920 Firefox/3.6.23'
            else:
                assert False
        assert row
        assert count == 1

def test_source_field_names():
    with apache.ApacheSource(
            EXAMPLE_03.splitlines(True),
            log_format="%{local}p,%{remote}p %{pid}P") as source:
        row = None
        for count, row in enumerate(source):
            assert row.local_port == [49600, 65000, 12345, 123][count]
            assert row.remote_port == [80, 80, 443, 443][count]
            assert row.pid == [1000, 2000, 65000, 100][count]
        assert row
        assert count == 3

def test_source_date_formats():
    with apache.ApacheSource(
            EXAMPLE_04.splitlines(True),
            log_format="%{%Y-%m-%dT%H:%M:%S%z}t %H %m %U%q %>s %O") as source:
        row = None
        for count, row in enumerate(source):
            if count == 0:
                assert row.time == dt.datetime('2004-03-08 00:56:39')
                assert row.method == 'GET'
                assert row.protocol == 'HTTP/1.0'
                assert row.url_stem == dt.url('/twiki/bin/view/Sandbox/WebHome')
                assert row.url_query == dt.url('?rev=1.6')
                assert row.status == 200
                assert row.bytes_sent == 8545
            elif count == 1:
                assert row.time == dt.datetime('2004-03-07 22:01:53')
                assert row.method == 'HEAD'
                assert row.protocol == 'HTTP/1.1'
                assert row.url_stem == dt.url('/razor.html')
                assert row.url_query is None
                assert row.status == 302
                assert row.bytes_sent == 2869
        assert row
        assert count == 1

def test_source_bad_formats(recwarn):
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%b %B'):
            pass
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%Q %x'):
            pass
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%C'):
            pass
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%{foo}p'):
            pass
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%{rid}P'):
            pass
    with pytest.raises(ValueError):
        with apache.ApacheSource('', log_format='%{%H%:%M:%S}t'):
            pass                                  #  ^ Extraneous percent
    with apache.ApacheSource(
            MULTIPLE_REMOTE_HOSTS.splitlines(True), log_format=apache.COMBINED) as source:
        for row in source:
            break
    assert recwarn.pop(apache.ApacheWarning)
    recwarn.clear()
    with apache.ApacheSource(
            INVALID_REMOTE_HOST.splitlines(True), log_format=apache.COMBINED) as source:
        for row in source:
            break
    assert recwarn.pop(apache.ApacheWarning)

