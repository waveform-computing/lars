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

"""
This module provides a target wrapper for CSV (Comma Separated Values)
formatted text files, which are typically used as a generic source format for
bulk loading databases.

The :class:`CSVTarget` class is the major element that this module provides; it
is a standard target class (a context manager with a
:meth:`~lars.csv.CSVTarget.write` method that accepts row tuples).


Classes
=======

.. autoclass:: CSVTarget(fileobj, header=False, dialect=CSV_DIALECT, encoding='utf-8', **kwargs)
   :members:

.. class:: CSV_DIALECT

    This is the default dialect used by the :class:`CSVTarget` class which has
    the following attributes:

    ============== ===============================
    Attribute      Value
    ============== ===============================
    delimiter      ``','`` (comma)
    quotechar      ``'"'`` (double-quote)
    quoting        :data:`QUOTE_MINIMAL`
    lineterminator ``'\\r\\n'`` (DOS line breaks)
    doublequote    True
    escapechar     None
    ============== ===============================

    This dialect is compatible with Microsoft Excel and the vast majority of
    of other products which accept CSV as an input format. However, please note
    that some UNIX based database products require UNIX style line endings
    (``'\\n'``) in which case you may wish to override the *lineterminator*
    attribute (see :class:`CSVTarget` for more information).

.. class:: TSV_DIALECT

    This is a dialect which produces tab-delimited files, another common data
    exchange format also supported by Microsoft Excel and numerous database
    products. This dialect has the following properties:

    ============== ===============================
    Attribute      Value
    ============== ===============================
    delimiter      ``'\\t'`` (tab)
    quotechar      ``'"'`` (double-quote)
    quoting        :data:`QUOTE_MINIMAL`
    lineterminator ``'\\r\\n'`` (DOS line breaks)
    doublequote    True
    escapechar     None
    ============== ===============================


Data
====

.. data:: QUOTE_NONE

    This value indicates that no values should ever be quoted, even if they
    contain the delimiter character. In this case, any delimiter characters
    appearing the data will be preceded by the dialect's *escapechar* which
    should be set to an appropriate value. If *escapechar* is not set (None)
    an exception will be raised if any character that require quoting are
    encountered.

.. data:: QUOTE_MINIMAL

    This is the default quoting mode. In this mode the writer will only quote
    those values that contain the *delimiter* or *quotechar* characters, or
    any of the characters in *lineterminator*.

.. data:: QUOTE_NONNUMERIC

    This value tells the writer to quote all numeric (int and float) values.

.. data:: QUOTE_ALL

    This value simply tells the writer to quote all values written.


Examples
========

A typical example of working with the class is shown below::

    import io
    from lars import apache, csv

    with io.open('/var/log/apache2/access.log', 'rb') as infile:
        with io.open('apache.csv', 'wb') as outfile:
            with apache.ApacheSource(infile) as source:
                with csv.CSVTarget(outfile, lineterminator='\\n') as target:
                    for row in source:
                        target.write(row)

"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import logging
import codecs
try:
    from backports import csv as csv_
except ImportError:
    import csv as csv_

str = type('')  # pylint: disable=redefined-builtin,invalid-name
try:
    long
except NameError:
    long = int  # pylint: disable=redefined-builtin,invalid-name

CSV_DIALECT = csv_.excel
TSV_DIALECT = csv_.excel_tab

QUOTE_ALL = csv_.QUOTE_ALL
QUOTE_NONE = csv_.QUOTE_NONE
QUOTE_MINIMAL = csv_.QUOTE_MINIMAL
QUOTE_NONNUMERIC = csv_.QUOTE_NONNUMERIC


class CSVSource(object):
    # TODO Code CSVSource
    # pylint: disable=missing-docstring,too-few-public-methods
    pass


class CSVTarget(object):
    """
    Wraps a stream to format rows as CSV (Comma Separated Values).

    This wrapper provides a simple :meth:`write` method which can be used to
    format row tuples as comma separated values in a variety of common
    dialects. The dialect defaults to :data:`CSV_DIALECT` which produces a
    typical CSV file compatible with the vast majority of products.

    If you desire a different output format you can either specify a different
    value for the *dialect* parameter, or if you only wish to use a minimal
    modification of the dialect you can override its attributes with keyword
    arguments. For example::

        CSVTarget(outfile, dialect=CSV_DIALECT, lineterminator='\\n')

    The *encoding* parameter controls the character set used in the output.
    This defaults to UTF-8 which is a sensible default for most modern systems,
    but is a multi-byte encoding which some legacy systems (notably mainframes)
    may have troubles with. In this case you can either select a single byte
    encoding like ISO-8859-1 or even EBCDIC. See `Python standard encodings`_
    for a full list of supported encodings.

    .. warning::

        The file that you wrap with :class:`CSVTarget` *must* be opened in
        binary mode (``'wb'``) partly because the dialect dictates the line
        terminator that is used, and partly because the class handles its own
        character encoding.

    .. _Python standard encodings: http://docs.python.org/2/library/codecs.html#standard-encodings
    """
    # pylint: disable=too-few-public-methods,too-many-instance-attributes

    def __init__(
            self, fileobj, header=False, dialect=CSV_DIALECT, encoding='utf-8',
            **kwargs):
        self.fileobj = fileobj
        self.header = header
        self.dialect = dialect
        self.encoding = encoding
        self.keywords = kwargs
        self.count = 0
        self._first_row = None
        # The csv writer outputs strings so we stick a transcoding shim between
        # the writer and the output object
        self._writer = csv_.writer(
            codecs.getwriter(self.encoding)(self.fileobj),
            dialect=self.dialect, **self.keywords)

    def __enter__(self):
        logging.debug('Entering CSVTarget context')
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logging.debug('Exiting CSVTarget context')
        self.close()

    def close(self):
        """
        Closes the CSV output. Further calls to :meth:`write` are not permitted
        after calling this method.
        """
        logging.debug('Closing CSV target')
        self._writer = None
        self._first_row = None

    def write(self, row):
        """
        Write the specified *row* (a tuple of values) to the wrapped output.
        All provided rows must have the same number of elements. There is no
        need to convert elements of the tuple to :class:`str`; this will be
        handled implicitly.
        """
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
        self._writer.writerow(row)
        self.count += 1
