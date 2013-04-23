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
Provides a wrapper for W3C extended log files.

The draft standard for the `W3C Extended Log File Format`_ is not well written
(see the various notes and comments in the code); actual practice deviates from
the draft in certain areas, and the draft is deficient in describing what is
potentially permitted in various other areas.

Examples of the format as produced by IIS (the major user of the draft) can be
found on `MSDN`_. When maintaining the code below, please refer to both the
draft (for information on what *could* be included in W3C log files) as well as
the examples (for information on what typically *is* included in W3C log files,
even when it outright violates the draft), and bear in mind `Postel's Law`_.

The :class:`W3CWrapper` class is the major element that this module provides;
this is the class which wraps a file-like object containing a W3C formatted log
file and yields rows from it as tuples.

Reference
=========

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
from datetime import datetime
from collections import namedtuple



def sanitize_name(name):
    """
    Sanitizes the given name for use as a Python identifier.

    :param str name: The name to sanitize
    :returns str: The sanitized name, suitable for use as an identifier
    """
    if name == '':
        raise ValueError('Cannot sanitize a blank string')
    return re.sub(r'[^A-Za-z_]', '_', name[:1]) + re.sub(r'[^A-Za-z0-9_]+', '_', name[1:])


class W3CError(Exception):
    """
    Base class for W3CWrapper errors.

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
        super(W3CError, self).__init__(message, line_number, line)

    def __str__(self):
        result = super(W3CError, self).__str__()
        if self.line_number:
            result = '%s on line %d' % (result, self.line_number)
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


class W3CWrapper(object):
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

    :param source: A file-like object containing the source stream
    """

    def __init__(self, source):
        self.source = source
        self.version = None
        self.software = None
        self.remark = None
        self.start = None
        self.finish = None
        self.fields = []
        self.field_type = None

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
        if self._match(VERSION_RE, line):
            if self.version is not None:
                raise W3CVersionError('Found a second #Version directive')
            self.version = self._result.group('text')
            if self.version != '1.0':
                raise W3CVersionError('Unknown W3C log version %s' % self.version)
        elif self._match(SOFTWARE_RE, line):
            self.software = self._result.group('text')
        elif self._match(REMARK_RE, line):
            self.remark = self._result.group('text')
        elif self._match(FIELDS_RE, line):
            self._process_fields(self._result.group('text'))
        elif self._match(START_DATE_RE, line):
            self.start = datetime.strptime(
                DATETIME_FORMAT,
                '%s %s' % (self._result.group('date'), self._result.group('time'))
                )
        elif self.match(END_DATE_RE, line):
            self.finish = datetime.strptime(
                DATETIME_FORMAT,
                '%s %s' % (self._result.group('date'), self._result.group('time'))
                )
        elif self.match(DATE_RE, line):
            self.date = datetime.strptime(
                DATETIME_FORMAT,
                '%s %s' % (self._result.group('date'), self._result.group('time'))
                )

    # The following insanely complicated regex is intended to match a single
    # header name within the #Fields specification of a W3C log file. Basically
    # headers come in one of three varieties:
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

    # The following attributes define regexes for each of the datatypes
    # specified in the W3C draft. Each regex includes an alternative for an
    # empty case (a single dash).
    #
    # Note that the regex for the "string" type deviates from the draft's
    # specifications; in practice IIS always URI encodes the content of
    # prefix(header) fields but the draft demands a "quoted string" format
    # instead. The draft also demands that the usual empty-field notation of a
    # dash ("-") is not used for "string" type fields (presumably an empty pair
    # of quotes should be used, although the draft doesn't explicitly state
    # this), but, again, practice deviates from this.

    TYPES_RE = {
        'date': re.compile(r'(-|\d{4}-\d{2}-\d{2})'),
        'time': re.compile(r'(-|\d{2}:\d{2}:\d{2})'),
        }

    def _process_fields(self, line):
        """
        Processes a ``#Fields`` directive.

        This method is responsible for configuring a regex for matching data
        rows, and a namedtuple to organize the content of data rows, based on
        the fields defined in the ``#Fields`` header directive.

        :param str line: The content of the ``#Fields`` directive
        """
        if self.fields:
            raise W3CFieldsError('Second #Fields directive found')
        fields = FIELD_RE.findall(line)
        row_regex = ''
        tuple_fields = []
        for prefix, header, identifier in fields:
            if header:
                original_name = '%s(%s)' % (prefix, identifier)
                python_name = sanitize_name('%s_%s' % (prefix, identifier))
            elif prefix:
                original_name = '%s-%s' % (prefix, identifier)
                python_name = sanitize_name('%s_%s' % (prefix, identifier))
            else:
                original_name = identifier
                python_name = sanitize_name(identifier)
            if original_name in self.fields:
                raise W3CFieldsError('Duplicate field name %s' % original_name)
            self.fields.append(original_name)
            tuple_fields.append(python_name)

    def _match(self, regex, line):
        """
        Match line against regex and cache the result in an instance variable.

        This utility method simply exists to permit a simple coding style in
        which a regex is tested against a line in an ``if`` statement and the
        match result is used in the body of the ``if`` statement without having
        to re-run the comparison.

        :param obj regex: The compiled regular expression object
        :param str line: The line to match against the regex object
        :returns: The match object or None if a match is not found
        """
        self._result = regex.match(line)
        return self._result

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
        for num, line in enumerate(self.source):
            try:
                if line.startswith('#'):
                    self._process_directive(line)
                else:
                    if self.version is None:
                        raise W3CVersionError(
                            'Missing #Version directive before data')
                    if not self.fields:
                        raise W3CFieldsError(
                            'Missing #Fields directive before data')
                    yield line.split(' ')
            except W3CError as exc:
                # Add line content and number to the exception and re-raise
                if not exc.line_number:
                    raise type(exc)(exc.args[0], line_number=num + 1, line=line)
                else:
                    raise
