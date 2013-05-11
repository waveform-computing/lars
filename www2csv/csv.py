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
Provides source and target wrappers for CSV-style files.

Reference
=========

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import io
import logging
import codecs
import csv


# Make Py2 str same as Py3
str = type('')


__all__ = [
    'QUOTE_ALL',
    'QUOTE_NONE',
    'QUOTE_MINIMAL',
    'QUOTE_NONNUMERIC',
    'CSVSource',
    'CSVTarget',
    ]


QUOTE_ALL = csv.QUOTE_ALL
QUOTE_NONE = csv.QUOTE_NONE
QUOTE_MINIMAL = csv.QUOTE_MINIMAL
QUOTE_NONNUMERIC = csv.QUOTE_NONNUMERIC


# Adapted from the official csv module's documentation:
class UnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f", which is encoded in the
    given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwds):
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode('utf-8') for s in row])
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)


class CSVSource(object):
    # TODO Code CSVSource
    pass


class CSVTarget(object):
    def __init__(
            self, fileobj, header=False, dialect=csv.excel, encoding='utf-8',
            **kwargs):
        self.fileobj = fileobj
        self.header = header
        self.dialect = dialect
        self.encoding = encoding
        self.keywords = kwargs
        self._first_row = None
        self._writer = None

    def __enter__(self):
        logging.debug('Entering CSVTarget context')
        logging.debug('Constructing CSV writer')
        self._writer = UnicodeWriter(
            self.fileobj, encoding=self.encoding, dialect=self.dialect,
            **self.keywords)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logging.debug('Exiting CSVTarget context')
        self._writer = None
        self._first_row = None

    def write(self, row):
        if self._first_row:
            if len(row) != len(self._first_row):
                raise TypeError('Rows must have the same number of elements')
        else:
            logging.debug('First row')
            self._first_row = row
            if self.header and hasattr(row, '_fields'):
                # XXX What if it doesn't have any _fields?
                logging.debug('Writing header row')
                self._writer.writerow(row._fields)
        self._writer.writerow([str(f) for f in row])

