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

"""
Provides a source and target wrappers for SQL-based databases.

This module provides wrappers which permit easy reading or writing of www-log
records from/to a SQL-based database. The :class:`SQLSource` class treats an
SQL query as the source of its log records, and provides an iterable which
yields rows in namedtuples. The :class:`SQLTarget` class accepts namedtuple
objects in its write method and automatically generates the required SQL
``INSERT`` or ``MERGE`` statements to append or merge records (respectively)
into the specified target table.

The implementation has been tested with SQLite3 (built into Python), and
PostgreSQL, but should work with any PEP-249 (Python DB API 2.0) compatible
database cursor.

Reference
=========
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )


class SQLSource(object):
    pass


class SQLTarget(object):
    def __init__(self, table, columns=None, mode='INSERT', paramstyle='qmark',
            commit=1000):
        self.table = table
        if columns is None:
            self.columns = ()
        else:
            self.columns = columns
        mode = mode.upper()
        if mode not in ('INSERT', 'MERGE'):
            raise ValueError('mode must be one of INSERT or MERGE')
        self.mode = mode
        self.paramstyle = paramstyle

    def write(self, row):
        # TODO Generate statement with placeholders (according to paramstyle)
        # TODO Assert len(row) == len(first_row)
        # XXX What to do with IP addresses and DNS names and URLs? str() seems best
        # TODO COMMIT every n (successful?) rows
        # XXX How do you know to COMMIT the last batch? Need a close() function?
        # XXX Or perhaps make a context handler for use with "with"...
