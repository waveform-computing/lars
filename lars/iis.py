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
This module provides a wrapper for W3C extended log files, typically used by
the Microsoft IIS web-server.

The :class:`IISSource` class is the major element that this module provides;
this is the class which wraps a file-like object containing a W3C formatted log
file and yields rows from it as tuples.


Classes
=======

.. autoclass:: IISSource
    :members:

    .. attribute:: count

        Returns the number of rows successfully read from the source

    .. attribute:: date

        The timestamp specified by the last encountered ``#Date`` directive (if
        any), as a :class:`~lars.datatypes.DateTime` instance

    .. attribute:: fields

        A sequence of fields names found in the ``#Fields`` directive in the
        file header

    .. attribute:: finish

        The timestamp found in the ``#End-Date`` directive (if any, as a
        :class:`~lars.datatypes.DateTime` instance)

    .. attribute:: remark

        The remarks recorded in the ``#Remark`` directive (if any)

    .. attribute:: software

        The name of the software which produced the source file as given by
        the ``#Software`` directive (if any)

    .. attribute:: start

        The timestamp found in the ``#Start-Date`` directive (if any), as a
        :class:`~lars.datatypes.DateTime` instance

    .. attribute:: version

        The version of the source file, as given by the ``#Version`` directive
        in the header


Exceptions
==========

.. autoclass:: IISError
   :members:

.. autoexception:: IISDirectiveError

.. autoexception:: IISFieldsError

.. autoexception:: IISVersionError

.. autoexception:: IISWarning


Examples
========

A typical usage of this class is as follows::

    import io
    from lars import iis, csv

    with io.open('logs\\iis.txt', 'rb') as infile:
        with io.open('iis.csv', 'wb') as outfile:
            with iis.IISSource(infile) as source:
                with csv.CSVTarget(outfile) as target:
                    for row in source:
                        target.write(row)


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
.. _MSDN: http://bit.ly/2lPjHfz
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
try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus  # pylint: disable=wrong-import-order

from . import parsers, datatypes as dt
from .exc import LarsError, LarsWarning

str = type('')  # pylint: disable=redefined-builtin,invalid-name


def _string_parse(s):
    """
    Parse a string in a IIS extended log format file.

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


class IISError(LarsError):
    """
    Base class for IISSource errors.

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
        super(IISError, self).__init__(message)

    def __str__(self):
        result = super(IISError, self).__str__()
        if self.line_number:
            result = 'Line %d: %s' % (self.line_number, result)
        return result


class IISDirectiveError(IISError):
    """
    Raised when an error is encountered in any ``#Directive``.
    """


class IISFieldsError(IISDirectiveError):
    """
    Raised when an error is encountered in a ``#Fields`` directive.
    """


class IISVersionError(IISDirectiveError):
    """
    Raised for a ``#Version`` directive with an unknown version is found.
    """


class IISWarning(LarsWarning):
    """
    Raised when an error is encountered in parsing a log row.
    """


class IISSource(object):
    """
    Wraps a stream containing a IIS formatted log file.

    This wrapper converts a stream containing a IIS formatted log file into an
    iterable which yields tuples. Each tuple is a namedtuple instance with the
    fieldnames of the tuple being the sanitized versions of the field names in
    the original log file (as specified in the ``#Fields`` directive).

    The directives contained in the file can be obtained from attributes of the
    wrapper itself (useful in the case that relative timestamps, e.g. with the
    ``#Date`` directive, are being used) in which case the attribute will be
    the lower-cased version of the directive name without the ``#`` prefix.

    :param source: A file-like object containing the source stream
    """
    # pylint: disable=too-many-instance-attributes,too-few-public-methods

    def __init__(self, source):
        self.source = source
        self.version = None
        self.software = None
        self.remark = None
        self.start = None
        self.finish = None
        self.date = None
        self.fields = []
        self.count = 0
        self._row_pattern = None
        self._row_funcs = None
        self._row_type = None

    # The following regexes are used to identify directives within IIS log
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

    # This is, apparently, the date format used by IIS log files. At least,
    # it's the format the draft dictates in the Date and Time sections, but
    # bizarrely the example in the Example section uses something quite
    # different (D-MMM-YYYY HH:MM:SS). However, every real-life example we've
    # seen to date follows the ISO(ish) format, so that's what we specify here.

    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    def _process_directive(self, line):
        """
        Processes a ``#Directive`` in a IIS log file.

        This method is called by the :meth:`__iter__` method when a
        ``#Directive`` line is encountered anywhere in a IIS log file
        (``#Directives`` can occur beyond the header, although it's rare to
        find them in practice). The method parses the ``#Directive`` and sets
        various instance attributes in response, the most important probably
        being ``#Version`` and ``#Fields`` which must occur before any data is
        encountered.

        :param str line: The directive line to process
        """
        logging.debug('Parsing directive: %s', line)
        directive = None
        for directive, regex in (
                ('Version', self.VERSION_RE),
                ('Software', self.SOFTWARE_RE),
                ('Remar', self.REMARK_RE),
                ('Fields', self.FIELDS_RE),
                ('Start-Date', self.START_DATE_RE),
                ('End-Date', self.END_DATE_RE),
                ('Date', self.DATE_RE),
        ):
            match = regex.match(line)
            if match:
                break
        else:
            raise IISDirectiveError('Unrecognized directive %s' %
                                    line.rstrip())

        if directive == 'Version':
            if self.version is not None:
                raise IISVersionError('Found a second #Version directive')
            self.version = match.group('text')
            if self.version != '1.0':
                raise IISVersionError('Unknown IIS log version %s' %
                                      self.version)
        elif directive == 'Software':
            self.software = match.group('text')
        elif directive == 'Remark':
            self.remark = match.group('text')
        elif directive == 'Fields':
            self._process_fields(match.group('text'))
        elif directive == 'Start-Date':
            self.start = dt.datetime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )
        elif directive == 'End-Date':
            self.finish = dt.datetime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )
        elif directive == 'Date':
            self.date = dt.datetime(
                '%s %s' % (match.group('date'), match.group('time')),
                self.DATETIME_FORMAT
                )

    # The FIELD_RE regex is intended to match a single header name within the
    # #Fields specification of a IIS log file. Basically headers come in one of
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
        'date':          'date_iso',
        'dns':           'hostname',
        'interval':      'integer',
        'ip':            'address_port',
        'method':        'hostname',  # No really, that's what the draft says!
        'status':        'integer',
        'time-from':     'time_iso',
        'time-taken':    'fixed',
        'time':          'time_iso',
        'time-to':       'time_iso',
        'uri-query':     'url',
        'uri-stem':      'url',
        'uri':           'url',
        # Extended IIS definitions
        'computername':  'string',
        'host':          'hostname',
        'port':          'integer',
        'sitename':      'string',
        'substatus':     'integer',
        'username':      'string',
        'version':       'string',
        'win32-status':  'integer',
        }

    # TYPES defines conversion functions and regexes for each of the datatypes
    # used in the W3C draft

    TYPES = {
        'integer':      (parsers.int_parse, parsers.INTEGER),
        'fixed':        (parsers.fixed_parse, parsers.FIXED),
        'date_iso':     (parsers.date_parse, parsers.DATE_ISO),
        'time_iso':     (parsers.time_parse, parsers.TIME_ISO),
        'url':          (parsers.url_parse, parsers.URL),
        # This regex deviates from the draft's specifications; in practice IIS
        # always URI encodes the content of prefix(header) fields but the draft
        # demands a "quoted string" format instead. The draft also demands that
        # the usual empty-field notation of a dash ("-") is not used for
        # "string" type fields (presumably an empty pair of quotes should be
        # used, although the draft doesn't explicitly state this), but, again,
        # practice deviates from this. This is very specific to the W3C format
        # so this isn't one of the standard regexes
        'string':       (_string_parse,
                         r'(?P<%(name)s>"([^"]|"")*"|[^"\s]\S*|-)'),
        # The draft dictates <alpha> for names, but firstly doesn't define what
        # <alpha> actually means; furthermore if we assume if means alphabetic
        # chars only (as seems reasonable) that's not even slightly sufficient
        # for validating DNS names (which is what this type is for), and
        # generally one expects that in the case of DNS resolution failure, an
        # IP address might be recorded in such fields too. Here we simply use
        # our default hostname regex
        'hostname':     (parsers.hostname_parse, parsers.HOSTNAME),
        # Again, the draft's BNF for an IP address is deficient (e.g. doesn't
        # specify a limit on octets, and isn't compatible with IPv6 which will
        # presumably start appearing in logs at some point), so we use our
        # generic address+port regex
        'address_port': (parsers.address_parse, parsers.ADDRESS_PORT),
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
            raise IISFieldsError('Second #Fields directive found')
        fields = self.FIELD_RE.findall(line)
        pattern = ''
        tuple_fields = []
        tuple_funcs = []
        for prefix, header, identifier in fields:
            # Figure out the original field name, a Python-ified version of
            # this name, and what type the field has
            if header:
                original_name = '%s(%s)' % (prefix, identifier)
                python_name = dt.sanitize_name('%s_%s' % (prefix, identifier))
                # According to the draft, all header fields are type <string>
                # but for user-friendliness we special-case Referr?er here
                if identifier.lower() in ('referer', 'referrer'):
                    field_type = 'url'
                else:
                    field_type = 'string'
            elif prefix:
                original_name = '%s-%s' % (prefix, identifier)
                python_name = dt.sanitize_name('%s_%s' % (prefix, identifier))
                # Default to <string> if we don't know the field identifier
                field_type = self.FIELD_TYPES.get(identifier, 'string')
            else:
                original_name = identifier
                python_name = dt.sanitize_name(identifier)
                field_type = self.FIELD_TYPES.get(identifier, 'string')
            if pattern:
                pattern += r'\s+'
            logging.debug('Field %s has type %s', original_name, field_type)
            field_fn, field_re = self.TYPES[field_type]
            pattern += field_re % {'name': python_name}
            tuple_funcs.append(field_fn)
            if original_name in self.fields:
                raise IISFieldsError('Duplicate field name %s' % original_name)
            self.fields.append(original_name)
            tuple_fields.append(python_name)
        logging.debug('Constructing row regex: %s', pattern)
        self._row_pattern = re.compile('^' + pattern + '$')
        logging.debug('Constructing row tuple with fields: %s',
                      ','.join(tuple_fields))
        self._row_type = dt.row(*tuple_fields)
        logging.debug('Constructing row parser functions')
        self._row_funcs = tuple_funcs

    def __enter__(self):
        logging.debug('Entering IIS context')
        self.count = 0
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        logging.debug('Exiting IIS context')

    def __iter__(self):
        """
        Yields a row tuple for each line in the file-like source object.

        This method is the main body of the class and is responsible for
        transforming lines from the source file-like object into row tuples.
        However, the main work of transforming strings into tuples is actually
        performed by the regular expressions and tuple class set up in response
        to encountering the ``#Fields`` directive in :meth:`_process_directive`
        above.
        """
        for num, line in enumerate(self.source):
            try:
                if line.startswith('#'):
                    self._process_directive(line.rstrip())
                elif self.version is None:
                    raise IISVersionError(
                        'Missing #Version directive before data')
                elif not self.fields:
                    raise IISFieldsError(
                        'Missing #Fields directive before data')
                else:
                    match = self._row_pattern.match(line.rstrip())
                    if match:
                        values = match.group(*self._row_type._fields)
                        try:
                            values = [f(v) for (f, v) in zip(self._row_funcs,
                                                             values)]
                        except ValueError as exc:
                            raise IISWarning(str(exc))
                        self.count += 1
                        yield self._row_type(*values)
                    else:
                        raise IISWarning('Line contains invalid data')
            except IISWarning as exc:
                # Add line number to the warning and report with warn()
                warnings.warn('Line %d: %s' % (num + 1, str(exc)), IISWarning)
            except IISError as exc:
                # Add line content and number to the exception and re-raise
                if not exc.line_number:
                    raise type(exc)(exc.args[0], line_number=num + 1,
                                    line=line)
                raise  # pragma: no cover
