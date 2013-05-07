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

from collections import namedtuple
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import pytest

from www2csv import csv, datatypes


# XXX Make Py2 str same as Py3
str = type('')

slow = pytest.mark.slow


def test_target():
    # Construct some test rows with appropriate namedtuples
    Row = namedtuple('Row', (
        'timestamp', 'client', 'method', 'url', 'time_taken', 'status',
        'size',
        ))
    row1 = Row(
        datatypes.datetime('2002-06-24 16:40:23'),
        datatypes.address('172.224.24.114'),
        'POST',
        datatypes.url('/Default.htm'),
        0.67,
        200,
        7930,
        )
    row2 = Row(
        datatypes.datetime('2002-05-02 20:18:01'),
        datatypes.address('172.22.255.255'),
        'GET',
        datatypes.url('/images/picture.jpg'),
        0.1,
        302,
        16328,
        )
    # Attempt to write to a StringIO buffer
    out = StringIO.StringIO()
    with csv.CSVTarget(out) as target:
        target.write(row1)
        target.write(row2)
        with pytest.raises(TypeError):
            target.write(('foo',))
    out = out.getvalue()
    assert len(out.splitlines()) == 2
    # Do it again, this time with a header
    out = StringIO.StringIO()
    with csv.CSVTarget(out, header=True) as target:
        target.write(row1)
        target.write(row2)
    out = out.getvalue()
    assert len(out.splitlines()) == 3
