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

from datetime import datetime, date, time

import pytest

from lars import parsers, datatypes


# Make Py2 str same as Py3
str = type('')


def test_url_parse():
    assert parsers.url_parse('-') is None
    assert parsers.url_parse('foo') == datatypes.Url('', '', 'foo', '', '', '')
    assert parsers.url_parse('//foo/bar') == datatypes.Url('', 'foo', '/bar', '', '', '')
    assert parsers.url_parse('http://foo/') == datatypes.Url('http', 'foo', '/', '', '', '')
    assert parsers.url_parse('http://foo/bar?baz=quux') == datatypes.Url('http', 'foo', '/bar', '', 'baz=quux', '')
    assert parsers.url_parse('https://foo/bar#baz') == datatypes.Url('https', 'foo', '/bar', '', '', 'baz')

def test_path_parse():
    assert parsers.path_parse('-') is None
    assert parsers.path_parse('/foo/bar/baz') == datatypes.Path('/foo/bar', 'baz', '')
    assert parsers.path_parse('/foo/bar.baz') == datatypes.Path('/foo', 'bar.baz', '.baz')
    assert parsers.path_parse('/foo/.baz') == datatypes.Path('/foo', '.baz', '')

def test_request_parse():
    assert parsers.request_parse('-') is None
    assert parsers.request_parse('OPTIONS * HTTP/1.0') == datatypes.Request('OPTIONS', None, 'HTTP/1.0')
    assert parsers.request_parse('GET /foo/bar HTTP/1.1') == datatypes.Request('GET', datatypes.url('/foo/bar'), 'HTTP/1.1')

def test_int_parse():
    assert parsers.int_parse('-') is None
    assert parsers.int_parse('0') == 0
    assert parsers.int_parse('-1') == -1
    assert parsers.int_parse('101') == 101
    with pytest.raises(ValueError):
        parsers.int_parse('abc')

def test_fixed_parse():
    assert parsers.fixed_parse('-') is None
    assert parsers.fixed_parse('0') == 0.0
    assert parsers.fixed_parse('0.') == 0.0
    assert parsers.fixed_parse('0.0') == 0.0
    assert parsers.fixed_parse('-101.5') == -101.5
    with pytest.raises(ValueError):
        parsers.fixed_parse('abc')

def test_date_parse():
    assert parsers.date_parse('-') is None
    assert parsers.date_parse('2000-01-01') == date(2000, 1, 1)
    assert parsers.date_parse('1986-02-28') == date(1986, 2, 28)
    with pytest.raises(ValueError):
        parsers.date_parse('1 Jan 2001')
    with pytest.raises(ValueError):
        parsers.date_parse('2000-01-32')
    with pytest.raises(ValueError):
        parsers.date_parse('abc')

def test_time_parse():
    assert parsers.time_parse('-') is None
    assert parsers.time_parse('12:34:56') == time(12, 34, 56)
    assert parsers.time_parse('00:00:00') == time(0, 0, 0)
    with pytest.raises(ValueError):
        parsers.time_parse('1:30:00 PM')
    with pytest.raises(ValueError):
        parsers.time_parse('25:00:30')
    with pytest.raises(ValueError):
        parsers.time_parse('abc')

def test_hostname_parse():
    assert parsers.hostname_parse('-') is None
    assert parsers.hostname_parse('foo') == 'foo'
    assert parsers.hostname_parse('foo.bar') == 'foo.bar'
    assert str(parsers.hostname_parse('127.0.0.1')) == '127.0.0.1'
    assert parsers.hostname_parse('f'*63 + '.o') == 'f'*63 + '.o'
    assert parsers.hostname_parse('f'*63 + '.oo') == 'f'*63 + '.oo'
    with pytest.raises(ValueError):
        parsers.hostname_parse('foo.')
    with pytest.raises(ValueError):
        parsers.hostname_parse('.foo.')
    with pytest.raises(ValueError):
        parsers.hostname_parse('-foo.bar')
    with pytest.raises(ValueError):
        parsers.hostname_parse('foo.bar-')
    with pytest.raises(ValueError):
        parsers.hostname_parse('f'*64 + '.o')
    with pytest.raises(ValueError):
        parsers.hostname_parse('foo.bar.'*32 + '.com')

def test_address_parse():
    assert parsers.address_parse('-') is None
    # All possible representations of an IPv4 address (including silly ones)
    assert str(parsers.address_parse('127.0.0.1')) == '127.0.0.1'
    assert str(parsers.address_parse('127.0.0.1:80')) == '127.0.0.1:80'
    assert str(parsers.address_parse('::1')) == '::1'
    assert str(parsers.address_parse('[::1]')) == '::1'
    assert str(parsers.address_parse('[::1]:80')) == '[::1]:80'
    assert str(parsers.address_parse('2001:0db8:85a3:0000:0000:8a2e:0370:7334')) == '2001:db8:85a3::8a2e:370:7334'
    assert str(parsers.address_parse('[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:22')) == '[2001:db8:85a3::8a2e:370:7334]:22'
    assert str(parsers.address_parse('[fe80::7334]:22')) == '[fe80::7334]:22'
    with pytest.raises(ValueError):
        parsers.address_parse('abc')
    with pytest.raises(ValueError):
        parsers.address_parse('google.com')
    with pytest.raises(ValueError):
        parsers.address_parse('127.0.0.1:100000')
    with pytest.raises(ValueError):
        parsers.address_parse('[::1]:100000')

