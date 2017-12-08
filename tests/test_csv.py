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

import io
from collections import namedtuple

import pytest

from lars import csv, datatypes


# XXX Make Py2 str same as Py3
str = type('')


@pytest.fixture
def rows():
    # Construct some test rows with appropriate namedtuples
    Row = namedtuple('Row', (
        'timestamp', 'client', 'method', 'url', 'time_taken', 'status',
        'size',
        ))
    return [
        Row(
            datatypes.datetime('2002-06-24 16:40:23'),
            datatypes.address('172.224.24.114'),
            'POST',
            datatypes.url('/Default.htm'),
            0.67,
            200,
            7930,
            ),
        Row(
            datatypes.datetime('2002-05-02 20:18:01'),
            datatypes.address('172.22.255.255'),
            'GET',
            datatypes.url('/images/picture.jpg'),
            0.1,
            302,
            16328,
            ),
        Row(
            datatypes.datetime('2002-05-29 12:34:56'),
            datatypes.address('9.180.235.203'),
            'HEAD',
            datatypes.url('/images/picture.jpg'),
            0.1,
            202,
            None,
            ),
        ]

def test_target(rows):
    # Attempt to write to a StringIO buffer
    out = io.BytesIO()
    with csv.CSVTarget(out) as target:
        for row in rows:
            target.write(row)
        with pytest.raises(TypeError):
            target.write(('foo',))
    out = out.getvalue().splitlines()
    assert len(out) == target.count
    assert out[0] == b'2002-06-24 16:40:23,172.224.24.114,POST,/Default.htm,0.67,200,7930'
    assert out[1] == b'2002-05-02 20:18:01,172.22.255.255,GET,/images/picture.jpg,0.1,302,16328'
    assert out[2] == b'2002-05-29 12:34:56,9.180.235.203,HEAD,/images/picture.jpg,0.1,202,'

def test_header(rows):
    # Do it again, this time with a header
    out = io.BytesIO()
    with csv.CSVTarget(out, header=True) as target:
        for row in rows:
            target.write(row)
    out = out.getvalue().splitlines()
    assert len(out) - 1 == target.count
    assert out[0] == b'timestamp,client,method,url,time_taken,status,size'
    assert out[1] == b'2002-06-24 16:40:23,172.224.24.114,POST,/Default.htm,0.67,200,7930'
    assert out[2] == b'2002-05-02 20:18:01,172.22.255.255,GET,/images/picture.jpg,0.1,302,16328'
    assert out[3] == b'2002-05-29 12:34:56,9.180.235.203,HEAD,/images/picture.jpg,0.1,202,'

def test_non_unicode(rows):
    # Do it with a non-utf-8 encoding to cover the full transcoding path
    out = io.BytesIO()
    with csv.CSVTarget(out, encoding='ascii') as target:
        for row in rows:
            target.write(row)
    out = out.getvalue()
    print(repr(out))
    out = out.splitlines()
    assert len(out) == target.count
    assert out[0] == b'2002-06-24 16:40:23,172.224.24.114,POST,/Default.htm,0.67,200,7930'
    assert out[1] == b'2002-05-02 20:18:01,172.22.255.255,GET,/images/picture.jpg,0.1,302,16328'
    assert out[2] == b'2002-05-29 12:34:56,9.180.235.203,HEAD,/images/picture.jpg,0.1,202,'

