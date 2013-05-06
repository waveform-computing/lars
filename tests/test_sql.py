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

import sqlite3
from collections import namedtuple

from nose.tools import assert_raises

from www2csv import sql, datatypes


# XXX Make Py2 str same as Py3
str = type('')


class FakeDbModule(object):
    def __init__(self):
        self.paramstyle = 'qmark'
        self.Error = StandardError


def test_target():
    # Test passing in deficient database modules
    db_module = FakeDbModule()
    del db_module.paramstyle
    assert_raises(NameError, sql.SQLTarget, db_module, None, 'foo')
    db_module = FakeDbModule()
    del db_module.Error
    assert_raises(NameError, sql.SQLTarget, db_module, None, 'foo')
    db_module = FakeDbModule()
    assert_raises(ValueError, sql.SQLTarget, db_module, None, 'foo', commit=0)
    # Construct an in-memory database for testing
    db = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)
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
    # Attempt a real load with DROP and CREATE TABLE. Drop should fail but be
    # ignored, as ignore_drop_errors is True
    with sql.SQLTarget(
            sqlite3, db, table='foo', create_table=True, drop_table=True,
            ignore_drop_errors=True) as target:
        target.write(row1)
        target.write(row2)
    cursor = db.cursor()
    # Ensure the table got created and contains 2 rows
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 2
    cursor.execute("SELECT * FROM foo WHERE method = 'POST'")
    data = cursor.fetchall()[0]
    assert data[0] == row1.timestamp
    assert data[1] == str(row1.client)
    assert data[2] == row1.method
    assert data[3] == str(row1.url)
    assert data[4] == row1.time_taken
    assert data[5] == row1.status
    assert data[6] == row1.size
    cursor.execute("SELECT * FROM foo WHERE method = 'GET'")
    data = cursor.fetchall()[0]
    assert data[0] == row2.timestamp
    assert data[1] == str(row2.client)
    assert data[2] == row2.method
    assert data[3] == str(row2.url)
    assert data[4] == row2.time_taken
    assert data[5] == row2.status
    assert data[6] == row2.size
    # Try again, also with DROP and CREATE TABLE, but with ignore_drop_errors
    # as False. The DROP should succeed silently this time. We also set commit
    # to 2 here which should force a commit on the second row
    with sql.SQLTarget(
            sqlite3, db, table='foo', commit=2, create_table=True,
            drop_table=True, ignore_drop_errors=False) as target:
        target.write(row1)
        target.write(row2)
    cursor = db.cursor()
    # Ensure the table still only contains 2 rows
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 2
