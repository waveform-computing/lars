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

import sqlite3
try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress
from collections import namedtuple

import pytest

from lars import sql, datatypes


# XXX Make Py2 str same as Py3
str = type('')


Row = namedtuple('Row', (
    'timestamp', 'client', 'method', 'url', 'time_taken', 'status', 'size',
    ))

@pytest.fixture
def db():
    # Construct an in-memory database for testing
    return sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES)

@pytest.fixture
def rows():
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

@pytest.fixture
def rows_null_first():
    return [
        Row(
            datatypes.datetime('2002-06-24 16:40:23'),
            datatypes.address('172.224.24.114'),
            None,
            None,
            0.01,
            408,
            0,
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

class FakeDbModule(object):
    def __init__(self):
        self.paramstyle = 'qmark'
        self.Error = Exception

def test_exceptions():
    exc = sql.SQLError('Something went wrong!', 1)
    assert str(exc) == 'Something went wrong! while processing row 1'
    exc = sql.SQLError('Something else went wrong!')
    assert str(exc) == 'Something else went wrong!'

def test_target_init():
    # Test passing in deficient database modules
    with pytest.raises(NameError):
        db_module = FakeDbModule()
        del db_module.paramstyle
        sql.SQLTarget(db_module, None, 'foo')
    with pytest.raises(NameError):
        db_module = FakeDbModule()
        del db_module.Error
        sql.SQLTarget(db_module, None, 'foo')
    with pytest.raises(ValueError):
        db_module = FakeDbModule()
        sql.SQLTarget(db_module, None, 'foo', commit=0)
    with pytest.raises(ValueError):
        db_module = FakeDbModule()
        sql.SQLTarget(db_module, None, 'foo', insert=0)
    with pytest.raises(ValueError):
        db_module = FakeDbModule()
        sql.SQLTarget(db_module, None, 'foo', commit=100, insert=13)

def test_target_write(db, rows):
    # Construct some test rows with appropriate namedtuples
    with sql.SQLTarget(sqlite3, db, table='foo', create_table=True) as target:
        target.write(rows[0])
        target.write(rows[1])
        target.write(rows[2])
        with pytest.raises(TypeError):
            target.write(('foo',))
    cursor = db.cursor()
    # Ensure the table got created and contains 2 rows which accurately reflect
    # the rows we fed in
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 3
    cursor.execute("SELECT * FROM foo WHERE method = ?", (rows[0].method,))
    data = cursor.fetchall()[0]
    assert data[0] == rows[0].timestamp
    assert data[1] == str(rows[0].client)
    assert data[2] == rows[0].method
    assert data[3] == str(rows[0].url)
    assert data[4] == rows[0].time_taken
    assert data[5] == rows[0].status
    assert data[6] == rows[0].size
    cursor.execute("SELECT * FROM foo WHERE method = ?", (rows[1].method,))
    data = cursor.fetchall()[0]
    assert data[0] == rows[1].timestamp
    assert data[1] == str(rows[1].client)
    assert data[2] == rows[1].method
    assert data[3] == str(rows[1].url)
    assert data[4] == rows[1].time_taken
    assert data[5] == rows[1].status
    assert data[6] == rows[1].size
    cursor.execute("SELECT * FROM foo WHERE method = ?", (rows[2].method,))
    data = cursor.fetchall()[0]
    assert data[0] == rows[2].timestamp
    assert data[1] == str(rows[2].client)
    assert data[2] == rows[2].method
    assert data[3] == str(rows[2].url)
    assert data[4] == rows[2].time_taken
    assert data[5] == rows[2].status
    assert data[6] == rows[2].size

def test_target_ip_integers(db, rows):
    # Test writing IP addresses as integers instead of strings
    with sql.SQLTarget(
            sqlite3, db, table='foo', create_table=True,
            ip_type='INTEGER') as target:
        target.write(rows[0])
        target.write(rows[1])
        target.write(rows[2])
    cursor = db.cursor()
    cursor.execute("SELECT client FROM foo WHERE method = ?", (rows[0].method,))
    assert cursor.fetchall()[0][0] == int(ipaddress.IPv4Address(rows[0].client))
    cursor.execute("SELECT client FROM foo WHERE method = ?", (rows[1].method,))
    assert cursor.fetchall()[0][0] == int(ipaddress.IPv4Address(rows[1].client))
    cursor.execute("SELECT client FROM foo WHERE method = ?", (rows[2].method,))
    assert cursor.fetchall()[0][0] == int(ipaddress.IPv4Address(rows[2].client))

def test_target_auto_drop(db, rows):
    # Test auto-DROP with a raise in the case the drop fails
    with pytest.raises(sql.SQLError):
        with sql.SQLTarget(
                sqlite3, db, 'foo', create_table=True, drop_table=True,
                ignore_drop_errors=False) as target:
            target.write(rows[0])
    # Test auto-DROP with ignored errors in case the drop fails
    with sql.SQLTarget(sqlite3, db, 'foo', create_table=True, drop_table=True,
            ignore_drop_errors=True) as target:
        target.write(rows[0])
    # Recreate the table, dropping the first
    with sql.SQLTarget(
            sqlite3, db, 'foo', create_table=True, drop_table=True,
            ignore_drop_errors=False) as target:
        target.write(rows[0])
        target.write(rows[1])
    # Check there's only two rows in the table
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 2
    # Target the same table without recreating it
    with sql.SQLTarget(sqlite3, db, 'foo') as target:
        target.write(rows[0])
    # Check there's now three rows in the table
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 3

def test_target_auto_commit(db, rows):
    with sql.SQLTarget(
            sqlite3, db, 'foo', create_table=True, commit=2) as target:
        target.write(rows[0])
        target.write(rows[1])
    # Check there's only two rows in the table
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM foo')
    assert cursor.fetchall()[0][0] == 2

def test_target_insert_error(db, rows):
    try:
        with sql.SQLTarget(sqlite3, db, 'foo', create_table=False) as target:
            target.write(rows[0])
    except Exception as e:
        # Check that the exception includes the row that generated the error
        assert e.row == rows[0]
        assert isinstance(e, sql.SQLError)

def test_target_multi_row_insert(db, rows):
    if sqlite3.sqlite_version_info >= (3, 7, 11):
        # Test multi-row INSERT if sqlite3 version supports it
        cursor = db.cursor()
        with sql.SQLTarget(
                sqlite3, db, 'foo', create_table=True, insert=2) as target:
            target.write(rows[0])
            cursor.execute('SELECT COUNT(*) FROM foo')
            assert cursor.fetchall()[0][0] == 0
            target.write(rows[1])
            cursor.execute('SELECT COUNT(*) FROM foo')
            assert cursor.fetchall()[0][0] == 2
            target.write(rows[2])
            cursor.execute('SELECT COUNT(*) FROM foo')
            assert cursor.fetchall()[0][0] == 2
        cursor.execute('SELECT COUNT(*) FROM foo')
        assert cursor.fetchall()[0][0] == 3
        cursor.execute('DROP TABLE foo')
        try:
            with sql.SQLTarget(
                    sqlite3, db, 'foo', create_table=False, insert=2) as target:
                target.write(rows[0])
        except Exception as e:
            # Check that when inserting multiple rows we don't bother to
            # include a specific row in exceptions that occur
            assert e.row is None
            assert isinstance(e, sql.SQLError)

def test_target_null_on_create(db, rows_null_first, recwarn):
    with sql.SQLTarget(sqlite3, db, table='foo', create_table=True) as target:
        target.write(rows_null_first[0])
        target.write(rows_null_first[1])
    assert recwarn.pop(sql.SQLWarning)
