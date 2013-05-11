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
This module provides a wrapper for W3C extended log files, typically used by
the Microsoft IIS web-server.

The :class:`W3CSource` class is the major element that this module provides;
this is the class which wraps a file-like object containing a W3C formatted log
file and yields rows from it as tuples.


Exceptions
==========

.. autoclass:: W3CError
   :members:

.. autoclass:: W3CDirectiveError

.. autoclass:: W3CFieldsError

.. autoclass:: W3CVersionError

.. autoclass:: W3CWarning


Classes
=======

.. autoclass:: W3CSource
   :members:


Note for maintainers
====================

The draft standard for the `W3C Extended Log File Format`_ is not well written
(see the various notes and comments in the code); actual practice deviates from
the draft in several areas, and the draft is deficient in describing what is
potentially permitted in other areas.

Examples of the format as produced by IIS (the major user of the draft) can be
found on `MSDN`_. When maintaining the code below, please refer to both the
draft (for information on what *could* be included in W3C log files) as well as
the examples (for information on what typically *is* included in W3C log files,
even when it outright violates the draft), and bear in mind `Postel's Law`_.


.. _W3C Extended Log File Format: http://www.w3.org/TR/WD-logfile.html
.. _MSDN: http://www.microsoft.com/technet/prodtechnol/WindowsServer2003/Library/IIS/ffdd7079-47be-4277-921f-7a3a6e610dcb.mspx
.. _Postel's Law: http://en.wikipedia.org/wiki/Robustness_principle
"""

from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

import re
import warnings
import logging
from datetime import datetime
from collections import namedtuple
from urllib import unquote_plus

from www2csv.datatypes import date, time, url, address, hostname


# Make Py2 str same as Py3
str = type('')


__all__ = [
    'W3CSource',
    'W3CError',
    'W3CDirectiveError',
    'W3CFieldsError',
    'W3CVersionError',
    'W3CWarning',
    ]


def sanitize_name(name):
    """
    Sanitizes the given name for use as a Python identifier.

    :param str name: The name to sanitize
    :returns str: The sanitized name, suitable for use as an identifier
    """
    if name == '':
        raise ValueError('Cannot sanitize a blank string')
    return re.sub(r'[^A-Za-z_]', '_', name[:1]) + re.sub(r'[^A-Za-z0-9_]+', '_', name[1:])


def url_parse(s):
    """
    Parse a URI string in a W3C extended log format file.

    This is a variant on the urlparse.urlparse function. The result type has
    been extended to include a :meth:`ParseResult.__str__` method which outputs
    the reconstructed URI.

    :param str s: The string containing the URI to parse
    :returns: A ParseResult tuple representing the URI
    """
    return url(s) if s != '-' else None


def int_parse(s):
    """
    Parse an integer string in a W3C extended log format file.

    This is a simple variant on int() that returns None in the case of a single
    dash being passed to s.

    :param str s: The string containing the integer number to parse
    :returns: An int value
    """
    return int(s) if s != '-' else None


def fixed_parse(s):
    """
    Parse an floating point string in a W3C extended log format file.

    This is a simple variant on float() that returns None in the case of a
    single dash being passed to s.

    :param str s: The string containing the floating point number to parse
    :returns: An float value
    """
    return float(s) if s != '-' else None


def date_parse(s):
    """
    Parse a date string in a W3C extended log format file.

    :param str s: The string containing the date to parse (YYYY-MM-DD format)
    :returns: A datetime.date object representing the date
    """
    return date(s) if s != '-' else None


def time_parse(s):
    """
    Parse a time string in a W3C extended log format file.

    :param str s: The string containing the time to parse (HH:MM:SS format)
    :returns: A datetime.time object representing the time
    """
    return time(s) if s != '-' else None


def string_parse(s):
    """
    Parse a string in a W3C extended log format file.

    Quoted strings have the external quotes stripped off and internal quotes,
    which are doubled for escaping purposes, halved. Unquoted strings are
    assumed to be URI %-encoded and are decoded as such.

    :param str s: The string to parse
    :returns: The decoded string
    """
    if s == '-':
        return None
    if s[:1] == '"':
        return s[1:-1].replace('""', '"')
    return unquote_plus(s)


def name_parse(s):
    """
    Verify a DNS name in a W3C extended log format file.

    :param str s: The string containing the DNS name to verify
    :returns: The verified string
    """
    return hostname(s) if s != '-' else None


def address_parse(s):
    """
    Verify an IPv4 or IPv6 address in a W3C extended log format file.

    :param str s: The string containing the address to verify
    :returns: The verified string
    """
    return address(s) if s != '-' else None


class W3CError(StandardError):
    """
    Base class for W3CSource errors.

    Exceptions of this class take the optional arguments line_number and line
    for specifying the index and content of the line that caused the error
    respectively. If specified, the :meth:`__str__` method is overridden to
    include the line number in the error message.

    :param str message: The error message
    :param int line_number: The 1-based index of the line that caused the error
    :param str line: The content of the line that caused the error
    """
    def __init__(self, message, line_number=None, line=None):
        self.line_number = line_number
        self.line = line
        super(W3CError, self).__init__(message)

    def __str__(self):
        result = super(W3CError, self).__str__()
        if self.line_number:
            result = 'Line %d: %s' % (self.line_number, result)
        return result


class W3CDirectiveError(W3CError):
    """
    Raised when an error is encountered in any ``#Directive``.
    """


class W3CFieldsError(W3CDirectiveError):
    """
    Raised when an error is encountered in a ``#Fields`` directive.
    """


class W3CVersionError(W3CDirectiveError):
    """
    Raised for a ``#Version`` directive with an unknown version is found.
    """


class W3CWarning(Warning):
    """
    Raised when an error is encountered in parsing a log row.
    """


class W3CSource(object):
    """
    Wraps a steam containing a W3C formatted log file.

    This wrapper converts a stream containing a W3C formatted log file into an
    iterable which yields tuples. Each tuple is a namedtuple instance with the
    fieldnames of the tuple being the sanitized versions of the field names in
    the original log file (as specified in the ``#Fields`` directive).

    The directives contained in the file can be obtained from attributes of the
    wrapper itself (useful in the case that relative timestamps, e.g. with the
    ``#Date`` directive, are being used) in which case the attribute will be
    the lower-cased version of the directive name without the ``#`` prefix.

    A typical usage of this class is as follows::

        import io
        from www2csv import w3c

        with io.open('source.txt', 'r') as infile:
            with w3c.W3CSource(infile) as source:
                for row in source:
                    # Do something with row
                    pass

    :param source: A file-like object containing the source stream
    """

    def __init__(self, source):
        self.source = source
        self.version = None
        self.software = None
        self.remark = None
        self.start = None
        self.finish = None
        self.date = None
        self.fields = []
        self._row_pattern = None
        self._row_funcs = None
        self._row_type = None

    # The following regexes are used to identify directives within W3C log
    # files. Contrary to popular opinion these can occur anywhere within the
    # log file; the draft places no limitations on where they can occur except
    # that #Version and #Fields directives must precede the first line of data.
    # This implementation assumes that a second #Fields directive is an error
    # but technically the draft does permit this (although we've never observed
    # it in practice).

    VERSION_RE = re.compile(
        r'^#\s*Version\s*:\s*(?P<text>\d+\.\d+)\s*$', flags=re.IGNORECASE)
    START_DATE_RE = re.compile(
        r'^#\s*Start-Date\s*:\s*(?P<date>\d{4}-\d{2}-\d{2})\s*'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s*$', flags=re.IGNORECASE)
    END_DATE_RE = re.compile(
        r'^#\s*End-Date\s*:\s*(?P<date>\d{4}-\d{2}-\d{2})\s*'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s*$', flags=re.IGNORECASE)
    DATE_RE = re.compile(
        r'^#\s*Date\s*:\s*(?P<date>\d{4}-\d{2}-\d{2})\s*'
        r'(?P<time>\d{2}:\d{2}:\d{2})\s*$', flags=re.IGNORECASE)
    SOFTWARE_RE = re.compile(
        r'^#\s*Software\s*:\s*(?P<text>.*)$', flags=re.IGNORECASE)
    REMARK_RE = re.compile(
        r'^#\s*Remark\s*:\s*(?P<text>.*)$', flags=re.IGNORECASE)
    FIELDS_RE = re.compile(
        r'^#\s*Fields\s*:\s*(?P<text>.*)$', flags=re.IGNORECASE)

    # This is, apparently, the date format used by W3C log files. At least,
    # it's the format the draft dictates in the Date and Time sections, but
    # bizarrely the example in the Example section uses something quite
    # different (D-MMM-YYYY HH:MM:SS). However, every real-life example we've
    # seen to date follows the ISO(ish) format, so that's what we specify here.

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def _process_directive(self, line):
        """
        Processes a ``#Directive`` in a W3C log file.

        This method is called by the :meth:`__iter__` method when a
        ``#Directive`` line is encountered anywhere in a W3C log file
        (``#Directives`` can occur beyond the header, although it's rare to
        find them in practice). The method parses the ``#Directive`` and sets
        various instance attributes in response, the most important probably
        being ``#Version`` and ``#Fields`` which must occur before any data is
        encountered.

        :param str line: The directive line to process
        """
        logging.debug('Parsing directive: %s', line)
        match = self.VERSION_RE.match(line)
        if match:
            if self.version is not None:
                raise W3CVersionError('Found a second #Version directive')
            self.version = match.group('text')
            if self.version != '1.0':
                raise W3CVersionError('Unknown W3C log version %s' % self.version)
            return
        match = self.SOFTWARE_RE.match(line)
        if match:
            self.software = match.group('text')
            return
        match = self.REMARK_RE.match(line)
        if match:
            self.remark = match.group('text')
            return
        match = self.FIELDS_RE.match(line)
        if match:
            self._process_fields(match.group('text'))
            return
        match = self.START_DATE_RE.match(line)
        if match:
            self.start = datetime.strptime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )
            return
        match = self.END_DATE_RE.match(line)
        if match:
            self.finish = datetime.strptime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )
            return
        match = self.DATE_RE.match(line)
        if match:
            self.date = datetime.strptime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )
            return
        raise W3CDirectiveError('Unrecognized directive %s' % line.rstrip())

    # The FIELD_RE regex is intended to match a single header name within the
    # #Fields specification of a W3C log file. Basically headers come in one of
    # three varieties:
    #
    #   * unprefixed, "identifier"
    #   * prefixed which take the form "prefix-ident"
    #   * HTTP header which take the form "prefix(header)"
    #
    # We limit the possible prefixes as the draft defines them, but we don't
    # place any limits on what characters can occur in the identifier as the
    # draft doesn't either (however, we do disallow space as otherwise there'd
    # be no way of differentiating a delimiter and a space in an identifier ...
    # sadly the draft doesn't even explicitly forbid this pathological case).

    FIELD_RE = re.compile(
        r'(?:(?P<prefix>[rc]s?|s[rc]?|x)'
        r'(?:-|(?P<header>\()))?'
        r'(?P<identifier>[^ ]+)(?(header)\))')

    # FIELD_TYPES maps a field's identifier (sans prefix) to a data-type
    # defined in the W3C draft. Any fields which are not mapped are assumed to
    # be type <string> (like all header fields which the draft explicitly
    # defines as having type <string>).
    #
    # The "extended IIS definitions" come from the IIS log definition, and from
    # MS KB909264 which details naming restrictions in Windows (the IIS log
    # definition isn't explicit about the types for things like site name and
    # computer name, aka NetBIOS name).

    FIELD_TYPES = {
        # Specified in the W3C draft standard
        'bytes':         'integer',
        'cached':        'integer',
        'comment':       'text',
        'count':         'integer',
        'date':          'date',
        'dns':           'name',
        'interval':      'integer',
        'ip':            'address',
        'method':        'name',
        'status':        'integer',
        'time-from':     'time',
        'time-taken':    'fixed',
        'time':          'time',
        'time-to':       'time',
        'uri-query':     'uri',
        'uri-stem':      'uri',
        'uri':           'uri',
        # Extended IIS definitions
        'computername':  'string',
        'host':          'name',
        'port':          'integer',
        'sitename':      'string',
        'substatus':     'integer',
        'username':      'string',
        'version':       'string',
        'win32-status':  'integer',
        }

    # TYPES_RE defines regexes for each of the datatypes specified in the W3C
    # draft. Each regex includes an alternative for an empty case (a single
    # dash).

    TYPES_RE = {
        # In the following regexes, there must be a single group which
        # covers the entire match. The group must be a named group with the
        # name %(name)s, which will be substituted for the Python-ified field
        # name in the regex constructed for row matching
        'integer': r'(?P<%(name)s>-|\d+)',
        'fixed':   r'(?P<%(name)s>-|\d+(\.\d*)?)',
        'date':    r'(?P<%(name)s>-|\d{4}-\d{2}-\d{2})',
        'time':    r'(?P<%(name)s>-|\d{2}:\d{2}:\d{2})',
        # Note - we do NOT try and validate URIs with this regex (as to do so
        # is incredibly complicated and much better left to a function), merely
        # perform some rudimentary extraction. The complex stuff on the left
        # side of the disjunction comes from RFC3986 appendix B. The reason for
        # the empty "-" production appearing on the right is due to an issue
        # with disjuncts in Perl-style regex implementations, see
        # <http://lingpipe-blog.com/2008/05/07/tokenization-vs-eager-regular-expressions/>
        # for details
        'uri':     r'(?P<%(name)s>(([^:/?#\s]+):)?(//([^/?#\s]*))?([^?#\s]*)(\?([^#\s]*))?(#(\S*))?|-)',
        # This regex deviates from the draft's specifications; in practice IIS
        # always URI encodes the content of prefix(header) fields but the draft
        # demands a "quoted string" format instead. The draft also demands that
        # the usual empty-field notation of a dash ("-") is not used for
        # "string" type fields (presumably an empty pair of quotes should be
        # used, although the draft doesn't explicitly state this), but, again,
        # practice deviates from this
        'string':  r'(?P<%(name)s>"([^"]|"")*"|[^"\s]\S*|-)',
        # The draft dictates <alpha> for names, but firstly doesn't define what
        # <alpha> actually means; furthermore if we assume if means alphabetic
        # chars only (as seems reasonable) that's not even slightly sufficient
        # for validating DNS names (which is what this type is for), and
        # generally one expects that in the case of DNS resolution failure, an
        # IP address might be recorded in such fields too. In fact, doing DNS
        # (or IP) validation is extremely hard to do properly with regexes so
        # here we use a trivial regex to pull out a string containing the right
        # alphabet and do validation in a later function
        'name':    r'(?P<%(name)s>-|[a-zA-Z0-9:.-]+)',
        # Again, the draft's BNF for an IP address is deficient (e.g. doesn't
        # specify a limit on octets, and isn't compatible with IPv6 which will
        # presumably start appearing in logs at some point), and again regex
        # validation of IP addresses is extremely hard to do properly so we
        # perform validation later in a function
        'address': r'(?P<%(name)s>-|([0-9]+(\.[0-9]+){3}|\[[0-9a-fA-F:]+\])(:[0-9]{1,5})?)',
        }

    # TYPES_FUNC defines, for each data-type given in the W3C draft standard, a
    # simple transformation function that converts the raw string extracted by
    # regex into some sensible data format (e.g. int for integer values, a date
    # object for date values, etc.)

    TYPES_FUNC = {
        'integer': int_parse,
        'fixed':   fixed_parse,
        'date':    date_parse,
        'time':    time_parse,
        'uri':     url_parse,
        'string':  string_parse,
        'name':    name_parse,
        'address': address_parse,
        }

    def _process_fields(self, line):
        """
        Processes a ``#Fields`` directive.

        This method is responsible for configuring a regex for matching data
        rows, and a namedtuple to organize the content of data rows, based on
        the fields defined in the ``#Fields`` header directive.

        :param str line: The content of the ``#Fields`` directive
        """
        logging.debug('Parsing #Fields: %s', line)
        if self.fields:
            raise W3CFieldsError('Second #Fields directive found')
        fields = self.FIELD_RE.findall(line)
        pattern = ''
        tuple_fields = []
        tuple_funcs = []
        for prefix, header, identifier in fields:
            # Figure out the original field name, a Python-ified version of
            # this name, and what type the field has
            if header:
                original_name = '%s(%s)' % (prefix, identifier)
                python_name = sanitize_name('%s_%s' % (prefix, identifier))
                # According to the draft, all header fields are type <string>
                field_type = 'string'
            elif prefix:
                original_name = '%s-%s' % (prefix, identifier)
                python_name = sanitize_name('%s_%s' % (prefix, identifier))
                # Default to <string> if we don't know the field identifier
                field_type = self.FIELD_TYPES.get(identifier, 'string')
            else:
                original_name = identifier
                python_name = sanitize_name(identifier)
                field_type = self.FIELD_TYPES.get(identifier, 'string')
            if pattern:
                pattern += r'\s+'
            logging.debug('Field %s has type %s', original_name, field_type)
            pattern += self.TYPES_RE[field_type] % {'name': python_name}
            tuple_funcs.append(self.TYPES_FUNC[field_type])
            if original_name in self.fields:
                raise W3CFieldsError('Duplicate field name %s' % original_name)
            self.fields.append(original_name)
            tuple_fields.append(python_name)
        logging.debug('Constructing row regex: ^%s$', pattern)
        self._row_pattern = re.compile('^' + pattern + '$')
        logging.debug('Constructing row tuple with fields: %s', ','.join(tuple_fields))
        self._row_type = namedtuple('row_type', tuple_fields)
        logging.debug('Constructing row parser functions')
        self._row_funcs = tuple_funcs

    def __enter__(self):
        logging.debug('Entering W3C context')
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logging.debug('Exiting W3C context')

    def __iter__(self):
        """
        Yields a row tuple for each line in the file-like source object.

        This method is the main body of the class and is responsible for
        transforming lines from the source file-like object into row tuples.
        However, the main work of transforming strings into tuples is actually
        performed by the regular expressions and namedtuple class set up in
        response to encountering the ``#Fields`` directive in
        :meth:`_process_directive` above.
        """
        # The main iterator loop is split into two. The reason for this is
        # simply performance. If everything is kept in one loop we wind up
        # redundantly testing whether we've seen the #Version and #Fields
        # header directives for *every single* data row. By splitting the loops
        # in this way we only test for them when required
        try:
            for num, line in enumerate(self.source):
                if line.startswith('#'):
                    self._process_directive(line.rstrip())
                elif self.version is None:
                    raise W3CVersionError(
                        'Missing #Version directive before data')
                elif not self.fields:
                    raise W3CFieldsError(
                        'Missing #Fields directive before data')
                else:
                    match = self._row_pattern.match(line.rstrip())
                    if match:
                        values = match.group(*self._row_type._fields)
                        try:
                            values = [f(v) for (f, v) in zip(self._row_funcs, values)]
                        except ValueError as exc:
                            raise W3CWarning(str(exc))
                        yield self._row_type(*values)
                    else:
                        raise W3CWarning('Line contains invalid data')
        except W3CWarning as exc:
            # Add line number to the warning and report with warn()
            warnings.warn('Line %d: %s' % (num + 1, str(exc)), W3CWarning)
        except W3CError as exc:
            # Add line content and number to the exception and re-raise
            if not exc.line_number:
                raise type(exc)(exc.args[0], line_number=num + 1, line=line)
            raise # pragma: no cover

