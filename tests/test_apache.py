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

import pytest

from www2csv import apache, datatypes


# Make Py2 str same as Py3
str = type('')


def test_english_locale():
    # Test we can simply instantiate the english-locale and that it has certain
    # attributes
    lt = apache.EnglishLocaleTime()
    attrs = ['a_month', 'a_weekday', 'f_month', 'f_weekday']
    for attr in attrs:
        assert hasattr(lt, attr)

def test_string_parse():
    assert apache.string_parse('-') is None
    assert apache.string_parse('') == ''
    assert apache.string_parse('abc') == 'abc'
    assert apache.string_parse('ab\\nc') == 'ab\nc'
    assert apache.string_parse('ab\\x0Ac') == 'ab\nc'
    assert apache.string_parse('foo\\tbar') == 'foo\tbar'
    assert apache.string_parse('foo\\x09bar') == 'foo\tbar'
    assert apache.string_parse('\\"foo\\"') == '"foo"'
    # Ensure the function simply leaves invalid escapes alone rather than
    # blowing up over them
    assert apache.string_parse('foo\\x') == 'foo\\x'
    assert apache.string_parse('foo\\xGG') == 'foo\\xGG'
    assert apache.string_parse('foo\\') == 'foo\\'

def test_time_parse():
    assert apache.time_parse('[25/Dec/1998:17:45:35 +0000]', apache.APACHE_TIME) == datatypes.DateTime(1998, 12, 25, 17, 45, 35)
    assert apache.time_parse('[25/Dec/1998:17:45:35 +0100]', apache.APACHE_TIME) == datatypes.DateTime(1998, 12, 25, 16, 45, 35)
    assert apache.time_parse('[4/Dec/2001:23:59:59 -0500]', apache.APACHE_TIME) == datatypes.DateTime(2001, 12, 5, 4, 59, 59)
    assert apache.time_parse('2000-01-01T12:34:56+0700', '%Y-%m-%dT%H:%M:%S%z') == datatypes.DateTime(2000, 1, 1, 5, 34, 56)
